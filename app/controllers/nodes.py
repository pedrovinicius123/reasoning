from ..schemas.nodes_schema import NodeSchema
from ..schemas.edges_schema import EdgeSchema
from ..models.node import Node
from ..models.edges import Edge
from ..utils.networkx_parser import NetworkxParser
from ..utils.response import successful_response
from ..extensions import db
from marshmallow import ValidationError
from werkzeug.exceptions import NotFound
from flask import request

node_schema = NodeSchema()
edge_schema = EdgeSchema()

nodes_schema = NodeSchema(many=True)
edges_schema = EdgeSchema(many=True)

def list_all_nodes():
    id = request.args.get("id", type=int)
    if id is None:
        raise ValidationError("graph id is required")

    nodes = Node.query.filter_by(graph_id=id).all()
    for node in nodes:
        print(node.label)
        print(node.desc)
    if not nodes:
        raise NotFound("Node db is empty for this graph id")

    return successful_response(nodes_schema.dump(nodes))

def list_all_edges():
    id = request.args.get("id", type=int)
    if id is None:
        raise ValidationError("graph id is required")

    edges = Edge.query.filter_by(graph_id=id).all()
    if not edges:
        raise NotFound("There are no edges")

    return successful_response(edges_schema.dump(edges))

def get_nid(id):
    node = Node.query.get_or_404(id)
    return successful_response(node_schema.dump(node))

def add_edge():
    data = request.json
    edge = data.get("edge", False)
    relation_type = data.get("relation")
    graph_id = data.get("graph_id", False)

    if edge and graph_id and relation_type in ["uni", "bi"]:
        p, c = set(edge)
        parent = Node.query.get_or_404(p)
        child = Node.query.get_or_404(c)

        if p == c:
            raise ValidationError("Node auto-referencing")
        
        # Get next edge id
        max_edge_id = db.session.query(db.func.max(Edge.id)).scalar() or 0
        edge_id = max_edge_id + 1
        
        edge = Edge(id=edge_id, parent=parent, child=child, relation=relation_type, graph_id=graph_id, penalty=.5)
        corr = Edge.query.filter_by(graph_id=graph_id, parent=parent, child=child).first()
        if not corr:
            db.session.add(edge)

        else:
            corr.relation = relation_type
            db.session.merge(corr)        
        db.session.commit()
    
    else:
        raise ValidationError("Invalid format")
    return successful_response("Edge created", 201)

def add_node():
    data = request.json
    node = node_schema.load(data)

    db.session.add(node)
    db.session.commit()       

    return successful_response(node_schema.dump(node), 201)     
