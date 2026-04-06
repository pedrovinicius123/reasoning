from ..utils.agents.creative import CreativeAgent
from ..utils.agents.critic import CriticAgent
from ..utils.response import successful_response
from ..utils.networkx_parser import NetworkxParserManger
from ..models.graph import Graph
from ..models.node import Node
from ..extensions import db
from ..schemas.edges_schema import EdgeSchema
from ..schemas.nodes_schema import NodeSchema
from ..schemas.agent_request_schemas import JsonRequestAgentSchemaCreative, JsonRequestAgentSchemaCritic
from flask import request


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

        parser.graph.add_edge(item["a"]["id"], item["b"]["id"], relation=item["relation"], penalty=item["penalty"])
        if item["relation"] == "bi":
            parser.graph.add_edge(item["b"]["id"], item["a"]["id"], relation=item["relation"], penalty=item["penalty"])

    print("Creation complete, now begin analysis with the critic agent...")
    output, parser = critic.interact(data["id"], parser=parser)
    if not output:
        parser.dump()
        return successful_response({"message": "No changes to be made"}, 200)
    
    # Add new nodes to the parser graph
    for node in output["new_nodes"]:
        parser.graph.add_node(node["id"], label=node["label"], desc=node["desc"], graph_id=data["id"])

    # Add new edges to the parser graph
    for edge in output["new_conns"]:
        parser.graph.add_edge(edge["a"], edge["b"], relation=edge["relation"], penalty=edge["penalty"])
        if edge["relation"] == "bi":
            parser.graph.add_edge(edge["b"], edge["a"], relation=edge["relation"], penalty=edge["penalty"])

    # Remove nodes from the parser graph
    for rm_node in output["nodes_to_delete"]:
        rm_node_id = rm_node["id"] if isinstance(rm_node, dict) else rm_node
        if rm_node_id in parser.graph:
            parser.graph.remove_node(rm_node_id)

    # Remove edges from the parser graph
    for rm_edge in output["conns_to_delete"]:
        parent_id = rm_edge["a"] if isinstance(rm_edge, dict) else rm_edge[0]
        child_id = rm_edge["b"] if isinstance(rm_edge, dict) else rm_edge[1]
        if parser.graph.has_edge(parent_id, child_id):
            parser.graph.remove_edge(parent_id, child_id)

    # Persist all changes back to the database
    parser.dump(output["nodes_to_delete"], output["conns_to_delete"])  
    return successful_response({"message": "Graph updated successfully"}, 201)

def develop_graph():
    data = request.json
    n_graphs = data.get("n_graphs", 5)
    initial_label = data.get("initial_label", "Node")
    initial_desc = data.get("initial_desc", "This is a node.")

    db.session.commit()
    manager = NetworkxParserManger()
    i = 0
    while i < 10:     
        for j in range(n_graphs):
            g = Graph.query.get(j+1)
            if not g:
                db.session.add(Graph())
                db.session.commit()

            if i == 0:
                node = Node(graph_id=j+1, label=f"{initial_label} {i}", desc=f"{initial_desc} {i}", is_primary=True)
                db.session.add(node)
                db.session.commit()
            data = {"id": j+1, "new_nodes": 3}
            output, parser = creative.interact(data["id"], data["new_nodes"])
            
            # Add new nodes from agent output to the parser graph
            for item in output["connections"]:
                parser.graph.add_node(item["a"]["id"], label=item["a"]["label"], desc=item["a"]["desc"], graph_id=data["id"])
                parser.graph.add_node(item["b"]["id"], label=item["b"]["label"], desc=item["b"]["desc"], graph_id=data["id"])
                
                parser.graph.add_edge(item["a"]["id"], item["b"]["id"], relation=item["relation"], penalty=item["penalty"])
                if item["relation"] == "bi":
                    parser.graph.add_edge(item["b"]["id"], item["a"]["id"], relation=item["relation"], penalty=item["penalty"])

            output, parser = critic.interact(data["id"], parser=parser)
            if not output:
                parser.dump()
                continue
            
            # Add new nodes to the parser graph
            for node in output["new_nodes"]:
                parser.graph.add_node(node["id"], label=node["label"], desc=node["desc"], graph_id=data["id"])

            # Add new edges to the parser graph
            for edge in output["new_conns"]:
                parser.graph.add_edge(edge["a"], edge["b"], relation=edge["relation"], penalty=edge["penalty"])
                if edge["relation"] == "bi":
                    parser.graph.add_edge(edge["b"], edge["a"], relation=edge["relation"], penalty=edge["penalty"])
            # Remove nodes from the parser graph
            for node in output["nodes_to_delete"]:
                if node["id"] in parser.graph:
                    parser.graph.remove_node(node["id"])
            # Remove edges from the parser graph
            for edge in output["conns_to_delete"]:
                if parser.graph.has_edge(edge["a"], edge["b"]):
                    parser.graph.remove_edge(edge["a"], edge["b"])
                if parser.graph.has_edge(edge["b"], edge["a"]):
                    parser.graph.remove_edge(edge["b"], edge["a"])
            
            parser.dump() 
        
        manager.dump_best()
        i += 1
