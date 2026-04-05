from ..utils.agents.creative import CreativeAgent
from ..utils.agents.critic import CriticAgent
from ..utils.response import successful_response
from ..models.node import Node
from ..models.edges import Edge
from ..extensions import db
from ..schemas.edges_schema import EdgeSchema
from ..schemas.nodes_schema import NodeSchema
from ..schemas.agent_request_schemas import JsonRequestAgentSchemaCreative, JsonRequestAgentSchemaCritic
from flask import request
import networkx as nx


creative = CreativeAgent()
critic = CriticAgent()
node_schema = NodeSchema()
edge_schema = EdgeSchema()
req_schema_creative = JsonRequestAgentSchemaCreative()
req_schema_critic = JsonRequestAgentSchemaCritic()

def interact_with_graph():
    data = req_schema_creative.load(request.get_json())
    output, parser = creative.interact(data["id"], data["new_nodes"])
    
    # Add new nodes from agent output to the parser graph
    for item in output["connections"]:
        print(item)
        parser.graph.add_node(item["a"]["id"], label=item["a"]["label"], desc=item["a"]["desc"], graph_id=data["id"])
        parser.graph.add_node(item["b"]["id"], label=item["b"]["label"], desc=item["b"]["desc"], graph_id=data["id"])

    # Add connections from agent output to the parser graph
    for item in output["connections"]:
        parser.graph.add_edge(item["a"]["id"], item["b"]["id"], relation=item["relation"], penalty=item["penalty"])
        if item["relation"] == "bi":
            parser.graph.add_edge(item["b"]["id"], item["a"]["id"], relation=item["relation"], penalty=item["penalty"])

    # Persist all changes back to the database
    parser.dump([])           
    return successful_response(output, 201)

def analyse_graph():
    data = req_schema_critic.load(request.get_json())
    output, parser = critic.interact(data["id"])
    
    # Add new nodes to the parser graph
    for node in output["new_nodes"]:
        parser.graph.add_node(node["id"], label=node["label"], desc=node["desc"], graph_id=data["id"])

    # Add new edges to the parser graph
    for edge in output["new_edges"]:
        parser.graph.add_edge(edge["a"]["id"], edge["b"]["id"], relation=edge["relation"], penalty=edge["penalty"])
        if edge["relation"] == "bi":
            parser.graph.add_edge(edge["b"]["id"], edge["a"]["id"], relation=edge["relation"], penalty=edge["penalty"])

    # Remove nodes from the parser graph
    for rm_node in output["rm_nodes"]:
        if rm_node in parser.graph:
            parser.graph.remove_node(rm_node)

    # Remove edges from the parser graph
    for rm_edge in output["rm_edges"]:
        if parser.graph.has_edge(rm_edge["a"]["id"], rm_edge["b"]["id"]):
            parser.graph.remove_edge(rm_edge["a"]["id"], rm_edge["b"]["id"])

    # Persist all changes back to the database
    parser.dump([])
    
    return successful_response(output)

