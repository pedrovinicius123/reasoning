import time

from flask import current_app, request

from ..schemas.agent_request_schemas import (
    JsonRequestAgentSchemaCreative,
    JsonRequestAgentSchemaCritic,
)
from ..schemas.edges_schema import EdgeSchema
from ..schemas.nodes_schema import NodeSchema
from ..utils.agents.creative import CreativeAgent, _limpar_formal_statement
from ..utils.networkx_parser import NetworkxParser, NetworkxParserManager
from ..utils.response import successful_response
from .parse_theorems import verify_proof

node_schema = NodeSchema()
edge_schema = EdgeSchema()
req_schema_creative = JsonRequestAgentSchemaCreative()
req_schema_critic = JsonRequestAgentSchemaCritic()

async def interact_with_graph(app_instance, task, n_graphs, generations, new_nodes_per_generation):
    with app_instance.app_context():        
        manager = NetworkxParserManager(task=task, n_graphs=n_graphs)
        graph, _ = NetworkxParser(graph_id=manager.graph_id).load()
        
        print(graph)
        creative = CreativeAgent()
        creative.task = task

        for _ in range(generations):
            for i in range(n_graphs):
                parsing = graph.copy()
                any_passed = False
                attempts = 0
                max_attempts = 10

                while not any_passed and attempts < max_attempts:
                    attempts += 1
                    results = await creative.interact(new_nodes_per_generation, graph=parsing)
                    if results == {}:
                        graph = parsing.copy()
                        parser = NetworkxParser(manager.graph_id)
                        parser.graph = graph
                        parser.dump()
                        print("parser dumped")

                        return  

                    # cap no histórico para não estourar o contexto
                    creative.past_errors = creative.past_errors[-30:]

                    batch_passed = False
                    for result in results["connections"]:
                        a, b = result["a"], result["b"]

                        r = await verify_proof(
                            _limpar_formal_statement(result["lean"]["formal_statement"]),
                            result["lean"]["content"],
                        )

                        if r.get("verified"):
                            batch_passed = True
                            parsing.add_node(a["id"], **{k: v for k, v in a.items() if k != "id"})
                            parsing.add_node(b["id"], **{k: v for k, v in b.items() if k != "id"})
                            parsing.nodes[a["id"]]["graph_id"] = manager.graph_id
                            parsing.nodes[b["id"]]["graph_id"] = manager.graph_id
                            parsing.add_edge(a["id"], b["id"],
                                            **{k: v for k, v in result.items() if k not in ("a", "b")})
                        else:
                            errors = r.get("errors") or [
                                f"verification failed for {a['id']}→{b['id']} {r.get("proof_errors")}"
                            ]
                            creative.past_errors.extend(errors)
                            print(errors)

                    # só marca sucesso DEPOIS do batch inteiro
                    if batch_passed:
                        any_passed = True
                        print("!")

                if not any_passed:
                    print(f"desisti após {max_attempts} tentativas para o grafo {i}")

                manager.set_parser_graph(i, parsing.copy())

            graph = manager.dump_best()
            print(graph)
            time.sleep(2)

async def start_interact_with_graph_thread():
    data = request.json
    app_obj_ = current_app._get_current_object()

    await interact_with_graph(app_obj_, data["task"], data["n_graphs"], data["generations"], data["new_nodes"])
    return successful_response({"message":"Reasoning thread started!"}, 201)
