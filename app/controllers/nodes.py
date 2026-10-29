from flask import request
from marshmallow import ValidationError
from werkzeug.exceptions import BadRequest, InternalServerError, NotFound

from ..extensions import db
from ..models.edges import Edge
from ..models.node import Node
from ..schemas.edges_schema import EdgeSchema
from ..schemas.nodes_schema import NodeSchema
from ..models.graph import Graph
from ..utils.response import successful_response

node_schema = NodeSchema()
edge_schema = EdgeSchema()

nodes_schema = NodeSchema(many=True)
edges_schema = EdgeSchema(many=True)

def list_graphs():
    graphs = Graph.query.order_by(Graph.id.desc()).all()
    return successful_response([
        {"id": graph.id, "task": graph.task, "nodes": len(graph.nodes), "edges": len(graph.edges)}
        for graph in graphs
    ])

def get_graph(graph_id):
    graph = Graph.query.get_or_404(graph_id)
    nodes = Node.query.filter_by(graph_id=graph_id).all()
    edges = Edge.query.filter_by(graph_id=graph_id).all()
    return successful_response({
        "id": graph.id,
        "task": graph.task,
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
    })

def list_all_nodes():
    try:
        id = request.args.get("id", type=int)
        if id is None:
            raise BadRequest("graph id is required")

        nodes = Node.query.filter_by(graph_id=id).all()
        if not nodes:
            raise NotFound("Node db is empty for this graph id")

        return successful_response(nodes_schema.dump(nodes))
    except (BadRequest, NotFound):
        raise
    except Exception as e:
        raise InternalServerError(f"An unexpected error occurred: {str(e)}")

def list_all_edges():
    try:
        id = request.args.get("id", type=int)
        if id is None:
            raise BadRequest("graph id is required")

        edges = Edge.query.filter_by(graph_id=id).all()
        if not edges:
            raise NotFound("There are no edges")

        return successful_response(edges_schema.dump(edges))
    except (BadRequest, NotFound):
        raise
    except Exception as e:
        raise InternalServerError(f"An unexpected error occurred: {str(e)}")

def get_nid(id):
    try:
        node = Node.query.get_or_404(id)
        return successful_response(node_schema.dump(node))
    except Exception as e:
        raise InternalServerError(f"An unexpected error occurred: {str(e)}")

def add_edge():
    try:
        data = request.json
        edge = data.get("edge")
        relation_type = data.get("relation")
        graph_id = data.get("graph_id")
        desc = data.get("desc", None)
        lean = data.get("lean", "")

        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            raise BadRequest("edge must be a list or tuple of two node ids")

        try:
            p, c = int(edge[0]), int(edge[1])
        except (TypeError, ValueError):
            raise BadRequest("edge node ids must be integers")

        try:
            graph_id = int(graph_id)
        except (TypeError, ValueError):
            raise BadRequest("graph_id must be an integer")

        if relation_type not in ["uni", "bi"]:
            raise BadRequest("relation must be 'uni' or 'bi'")

        parent = Node.query.get_or_404(p)
        child = Node.query.get_or_404(c)

        if parent.graph_id != graph_id or child.graph_id != graph_id:
            raise BadRequest("Both nodes must belong to the specified graph")

        if p == c:
            raise BadRequest("Node auto-referencing")

        existing_edge = Edge.query.filter_by(graph_id=graph_id, parent_id=p, child_id=c).first()
        if existing_edge:
            existing_edge.relation = relation_type
            existing_edge.desc = desc
            existing_edge.lean = lean
        else:
            new_edge = Edge(
                parent=parent,
                child=child,
                relation=relation_type,
                graph_id=graph_id,
                penalty=.5,
                desc=desc,
                lean=lean,
            )
            db.session.add(new_edge)

        if relation_type == "bi":
            existing_reverse = Edge.query.filter_by(graph_id=graph_id, parent_id=c, child_id=p).first()
            if existing_reverse:
                existing_reverse.relation = relation_type
                existing_reverse.desc = desc
                existing_reverse.lean = lean
            else:
                reverse_edge = Edge(
                    parent=child,
                    child=parent,
                    relation=relation_type,
                    graph_id=graph_id,
                    penalty=.5,
                    desc=desc,
                    lean=lean,
                )
                db.session.add(reverse_edge)
        
        db.session.commit()
        return successful_response("Edge created", 201)
    except (BadRequest, NotFound):
        raise
    except Exception as e:
        db.session.rollback()
        raise InternalServerError(f"Database error: {str(e)}")

def del_edge():
    try:
        data = request.json
        edge = data.get("edge")
        graph_id = data.get("graph_id")

        if not isinstance(edge, (list, tuple)) or len(edge) != 2:
            raise BadRequest("edge must be a list or tuple of two node ids")

        try:
            p, c = int(edge[0]), int(edge[1])
        except (TypeError, ValueError):
            raise BadRequest("edge node ids must be integers")

        try:
            graph_id = int(graph_id)
        except (TypeError, ValueError):
            raise BadRequest("graph_id must be an integer")

        edge_to_delete = Edge.query.filter_by(graph_id=graph_id, parent_id=p, child_id=c).first()
        if not edge_to_delete:
            raise NotFound("Edge not found")

        db.session.delete(edge_to_delete)

        reverse_edge = Edge.query.filter_by(graph_id=graph_id, parent_id=c, child_id=p).first()
        if reverse_edge:
            db.session.delete(reverse_edge)

        db.session.commit()
        return successful_response("Edge deleted", 200)
    except (BadRequest, NotFound):
        raise
    except Exception as e:
        db.session.rollback()
        raise InternalServerError(f"Database error: {str(e)}")

def del_graph():
    try:
        graph_id = request.args.get("id", type=int)
        if graph_id is None:
            raise BadRequest("graph_id is required")

        edges_deleted = Edge.query.filter_by(graph_id=graph_id).delete()
        nodes_deleted = Node.query.filter_by(graph_id=graph_id).delete()
        db.session.commit()

        return successful_response({"message": f"Graph {graph_id} cleared. Deleted {nodes_deleted} nodes and {edges_deleted} edges."}, 200)
    except (BadRequest):
        raise
    except Exception as e:
        db.session.rollback()
        raise InternalServerError(f"Database error: {str(e)}")

def delete_graph_record(graph_id):
    graph = Graph.query.get_or_404(graph_id)
    edges_deleted = Edge.query.filter_by(graph_id=graph_id).delete(synchronize_session=False)
    nodes_deleted = Node.query.filter_by(graph_id=graph_id).delete(synchronize_session=False)
    db.session.delete(graph)
    db.session.commit()

    return successful_response({
        "message": f"Graph {graph_id} deleted.",
        "deleted_nodes": nodes_deleted,
        "deleted_edges": edges_deleted,
    })

def add_node():
    try:
        data = request.json
        try:
            node = node_schema.load(data)
        except ValidationError as ve:
            raise BadRequest(f"Validation Error: {ve.messages}")

        db.session.add(node)
        db.session.commit()
        return successful_response(node_schema.dump(node), 201)
    except BadRequest:
        raise
    except Exception as e:
        db.session.rollback()
        raise InternalServerError(f"Database error: {str(e)}")
