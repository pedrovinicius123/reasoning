import asyncio
import json
import queue
import threading

from flask import Response, current_app, request, stream_with_context
from werkzeug.exceptions import BadRequest

from ..extensions import db
from ..models.edges import Edge
from ..models.graph import Graph
from ..models.node import Node
from ..utils.agents.creative import CreativeAgent, _limpar_formal_statement
from ..utils.agents.writer import WriterAgent
from ..utils.networkx_parser import NetworkxParser, NetworkxParserManager, normalize_node_label
from ..utils.response import successful_response
from .parse_theorems import verify_proof

SSE_HEARTBEAT_SECONDS = 10


def _validate_reasoning_request(data):
    if not isinstance(data, dict):
        raise BadRequest("JSON object required")
    task = data.get("task")
    if not isinstance(task, str) or not task.strip() or len(task) > 256:
        raise BadRequest("task must contain 1 to 256 characters")

    values = {}
    for key, default, minimum, maximum in (
        ("n_graphs", 1, 1, 5),
        ("generations", 1, 1, 20),
        ("new_nodes", 3, 1, 10),
    ):
        value = data.get(key, default)
        if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
            raise BadRequest(f"{key} must be an integer between {minimum} and {maximum}")
        values[key] = value
    return task.strip(), values["n_graphs"], values["generations"], values["new_nodes"]


def _graph_payload(graph_id):
    nodes = Node.query.filter_by(graph_id=graph_id).all()
    edges = Edge.query.filter_by(graph_id=graph_id).all()
    return {
        "graph_id": graph_id,
        "nodes": [
            {"id": node.id, "label": node.label, "desc": node.desc, "is_primary": node.is_primary}
            for node in nodes
        ],
        "edges": [
            {
                "id": edge.id,
                "source": edge.parent_id,
                "target": edge.child_id,
                "relation": edge.relation,
                "penalty": edge.penalty,
                "desc": edge.desc or "",
            }
            for edge in edges
        ],
    }


def _stream_node_id(node_id):
    if isinstance(node_id, int) and node_id < 0:
        return f"pending-{abs(node_id)}"
    return node_id


async def interact_with_graph(task, n_graphs, generations, new_nodes_per_generation, emit=None):
    manager = NetworkxParserManager(task=task, n_graphs=n_graphs)
    graph, _ = NetworkxParser(graph_id=manager.graph_id).load()
    creative = CreativeAgent(task=task)
    next_temporary_id = -1

    if emit:
        emit({"type": "start", "graph_id": manager.graph_id, "task": task})

    for generation in range(generations):
        node_ids_by_label = {
            normalize_node_label(attributes.get("label", "")): node_id
            for node_id, attributes in graph.nodes(data=True)
            if normalize_node_label(attributes.get("label", ""))
        }
        for graph_index in range(n_graphs):
            parsing = graph.copy()
            any_passed = False
            attempts = 0

            while not any_passed and attempts < 10:
                attempts += 1
                if emit:
                    emit({
                        "type": "progress",
                        "graph_id": manager.graph_id,
                        "generation": generation + 1,
                        "graph_index": graph_index + 1,
                        "attempt": attempts,
                    })
                results = await creative.interact(new_nodes_per_generation, graph=parsing)
                if results == {}:
                    any_passed = True
                    break

                verified_count = 0

                for result in results["connections"]:
                    a, b = result["a"], result["b"]
                    for node in (a, b):
                        label_key = normalize_node_label(node["label"])
                        if label_key and label_key in node_ids_by_label:
                            node["id"] = node_ids_by_label[label_key]
                        elif node["id"] in parsing and normalize_node_label(
                            parsing.nodes[node["id"]].get("label", "")
                        ) == label_key:
                            node_ids_by_label[label_key] = node["id"]
                        else:
                            node["id"] = next_temporary_id
                            next_temporary_id -= 1
                            if label_key:
                                node_ids_by_label[label_key] = node["id"]

                    if a["id"] == b["id"]:
                        continue

                    try:
                        verification = await verify_proof(
                            _limpar_formal_statement(result["lean"]["formal_statement"]),
                            result["lean"]["content"],
                        )
                    except (KeyError, TypeError) as error:
                        verification = {"verified": False, "errors": [f"Invalid Lean payload: {error}"]}

                    if verification.get("verified"):
                        verified_count += 1
                        for node in (a, b):
                            if node["id"] not in parsing:
                                parsing.add_node(
                                    node["id"],
                                    **{key: value for key, value in node.items() if key != "id"},
                                    graph_id=manager.graph_id,
                                )
                        parsing.add_edge(
                            a["id"], b["id"],
                            **{key: value for key, value in result.items() if key not in ("a", "b")},
                        )
                    else:
                        creative.past_errors.extend(
                            verification.get("errors") or verification.get("proof_errors") or ["Proof verification failed"]
                        )

                if verified_count:
                    any_passed = True
                    if emit:
                        emit({
                            "type": "batch",
                            "graph_id": manager.graph_id,
                            "generation": generation + 1,
                            "graph_index": graph_index + 1,
                            "verified_connections": verified_count,
                            "graph": {
                                "nodes": [
                                    {"id": _stream_node_id(node_id), **attributes}
                                    for node_id, attributes in parsing.nodes(data=True)
                                ],
                                "edges": [
                                    {
                                        "source": _stream_node_id(source),
                                        "target": _stream_node_id(target),
                                        **attributes,
                                    }
                                    for source, target, attributes in parsing.edges(data=True)
                                ],
                            },
                        })

            manager.set_parser_graph(graph_index, parsing.copy())

        graph = manager.dump_best()
        if emit:
            emit({"type": "graph", **_graph_payload(manager.graph_id)})

    return manager.graph_id


def stream_reasoning():
    task, n_graphs, generations, new_nodes = _validate_reasoning_request(request.get_json(silent=True))
    app = current_app._get_current_object()
    events = queue.Queue()

    def run():
        try:
            with app.app_context():
                try:
                    graph_id = asyncio.run(
                        interact_with_graph(task, n_graphs, generations, new_nodes, emit=events.put)
                    )
                    events.put({"type": "complete", "graph_id": graph_id})
                except Exception as error:
                    db.session.rollback()
                    app.logger.exception("Reasoning stream failed")
                    events.put({"type": "error", "message": str(error) or type(error).__name__})
        except Exception as error:
            app.logger.exception("Could not initialize reasoning stream context")
            events.put({"type": "error", "message": str(error) or type(error).__name__})
        finally:
            events.put(None)

    threading.Thread(target=run, daemon=True).start()

    @stream_with_context
    def generate():
        while True:
            try:
                event = events.get(timeout=SSE_HEARTBEAT_SECONDS)
            except queue.Empty:
                yield ": keep-alive\n\n"
                continue
            if event is None:
                break
            event_type = event.pop("type")
            yield f"event: {event_type}\ndata: {json.dumps(event, ensure_ascii=True)}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def write_graph():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("graph_id"), int):
        raise BadRequest("graph_id must be an integer")
    graph_record = Graph.query.get_or_404(data["graph_id"])
    graph, _ = NetworkxParser(graph_record.id).load()
    writer = WriterAgent(task=graph_record.task)
    return successful_response({"graph_id": graph_record.id, "output": writer.interact(graph)})


def stream_writer():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("graph_id"), int):
        raise BadRequest("graph_id must be an integer")
    graph_id = data["graph_id"]
    app = current_app._get_current_object()
    events = queue.Queue()

    def run():
        try:
            with app.app_context():
                try:
                    graph_record = Graph.query.get_or_404(graph_id)
                    graph, _ = NetworkxParser(graph_record.id).load()
                    WriterAgent(task=graph_record.task).interact(graph, on_chunk=events.put)
                    events.put({"type": "done", "graph_id": graph_id})
                except Exception as error:
                    db.session.rollback()
                    app.logger.exception("Writer stream failed")
                    events.put({"type": "error", "message": str(error) or type(error).__name__})
        except Exception as error:
            app.logger.exception("Could not initialize Writer stream context")
            events.put({"type": "error", "message": str(error) or type(error).__name__})
        finally:
            events.put(None)

    threading.Thread(target=run, daemon=True).start()

    @stream_with_context
    def generate():
        while True:
            try:
                event = events.get(timeout=SSE_HEARTBEAT_SECONDS)
            except queue.Empty:
                yield ": keep-alive\n\n"
                continue
            if event is None:
                break
            if isinstance(event, str):
                event = {"type": "delta", "text": event}
            event_type = event.pop("type")
            yield f"event: {event_type}\ndata: {json.dumps(event, ensure_ascii=True)}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
