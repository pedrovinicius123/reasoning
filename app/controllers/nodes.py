from ..schemas.nodes_schema import NodeSchema, Node
from ..schemas.edges_schema import EdgeSchema, Edge
from ..utils.networkx_parser import NetworkxParser
from ..utils.response import successful_response
from ..extensions import db
from marshmallow import ValidationError
from werkzeug.exceptions import NotFound
from flask import request

networkx_schema = NetworkxParser()
node_schema = NodeSchema()
edge_schema = EdgeSchema()

nodes_schema = NodeSchema(many=True)
edges_schema = EdgeSchema(many=True)

def list_all_nodes():
    nodes = Node.query.all()
    if not nodes:
        raise NotFound("Node db is empty")
    
    return successful_response(nodes_schema.dump(nodes))

def list_all_edges():
    edges = Edge.query.all()
    if not edges:
        raise NotFound("There are no edges")
    
    return successful_response(edges_schema.dump(edges))

def get_nid(id:int):
    node = Node.query.get_or_404(id)
    return successful_response(node_schema.dump(node))

def add_edge():
    data = request.json
    edge = data.get("edge", False)
    relation_type = data.get("relation")

    if edge:
        p, c = set(edge)
        parent = Node.query.get_or_404(p)
        child = Node.query.get_or_404(c)

        if p == c:
            raise ValidationError("Node auto-referencing")
        
        edge = Edge(parent=parent, child=child, relation=relation_type, penalty=.5)
        corr = Edge.query.filter_by(parent=parent, child=child).first()
        if not corr:
            db.session.add(edge)

        else:
            corr.relation = relation_type        
        db.session.commit()
    
    else:
        raise ValidationError("Invalid format")
    return successful_response("Edge created", 201)

def add_node():
    data = request.json
    node = node_schema.load(data)

    db.session.add(node)
    db.session.commit()       

    return successful_response("Node created", 201)     
