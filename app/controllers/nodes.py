from ..schemas.nodes_schema import NodeSchema
from ..schemas.edges_schema import EdgeSchema
from ..models.node import Node
from ..models.edges import Edge
from ..utils.networkx_parser import NetworkxParser
from ..utils.response import successful_response
from ..extensions import db
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import NotFound
from flask import request

node_schema = NodeSchema()
edge_schema = EdgeSchema()

nodes_schema = NodeSchema(many=True)
edges_schema = EdgeSchema(many=True)

def list_all_nodes():
    id = request.args.get("id", type=int)
    if id is None:
        raise BadRequest("graph id is required")

    nodes = Node.query.filter_by(graph_id=id).all()
    if not nodes:
        raise NotFound("Node db is empty for this graph id")

    return successful_response(nodes_schema.dump(nodes))

def list_all_edges():
    id = request.args.get("id", type=int)
    if id is None:
        raise BadRequest("graph id is required")

    edges = Edge.query.filter_by(graph_id=id).all()
    if not edges:
        raise NotFound("There are no edges")

    return successful_response(edges_schema.dump(edges))

def get_nid(id):
    node = Node.query.get_or_404(id)
    return successful_response(node_schema.dump(node))

def add_edge():
    data = request.json
    edge = data.get("edge")
    relation_type = data.get("relation")
    graph_id = data.get("graph_id")
    desc = data.get("desc", None)

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
        
    # Check if edge already exists
    existing_edge = Edge.query.filter_by(graph_id=graph_id, parent_id=p, child_id=c).first()
    if existing_edge:
        existing_edge.relation = relation_type
        existing_edge.desc = desc
    else:
        new_edge = Edge(parent=parent, child=child, relation=relation_type, graph_id=graph_id, penalty=.5, desc=desc)
        db.session.add(new_edge)
        
    # For bidirectional, also add the reverse edge
    if relation_type == "bi":
        existing_reverse = Edge.query.filter_by(graph_id=graph_id, parent_id=c, child_id=p).first()
        if existing_reverse:
            existing_reverse.relation = relation_type
            existing_reverse.desc = desc
        else:
            reverse_edge = Edge(parent=child, child=parent, relation=relation_type, graph_id=graph_id, penalty=.5, desc=desc)
            db.session.add(reverse_edge)
        
    db.session.commit()
    return successful_response("Edge created", 201)

def del_edge():
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
    
    # Also delete reverse edge if it exists
    reverse_edge = Edge.query.filter_by(graph_id=graph_id, parent_id=c, child_id=p).first()
    if reverse_edge:
        db.session.delete(reverse_edge)

    db.session.commit()
    return successful_response("Edge deleted", 200)

def del_graph():
    graph_id = request.args.get("id", type=int)
    if graph_id is None:
        raise BadRequest("graph_id is required")

    edges_deleted = Edge.query.filter_by(graph_id=graph_id).delete()
    nodes_deleted = Node.query.filter_by(graph_id=graph_id).delete()
    db.session.commit()

    return successful_response({"message": f"Graph {graph_id} cleared. Deleted {nodes_deleted} nodes and {edges_deleted} edges."}, 200)

def add_node():
    data = request.json
    node = node_schema.load(data)

    db.session.add(node)
    db.session.commit()       

    return successful_response(node_schema.dump(node), 201)     
