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
        parser.graph.add_node(item["a"]["id"], label=item["a"].get("label", ""), desc=item["a"].get("desc", ""), graph_id=data["id"])
        parser.graph.add_node(item["b"]["id"], label=item["b"].get("label", ""), desc=item["b"].get("desc", ""), graph_id=data["id"])

        parser.graph.add_edge(item["a"]["id"], item["b"]["id"], relation=item.get("relation", "uni"), penalty=item.get("penalty", 0.5))
        if item.get("relation") == "bi":
            parser.graph.add_edge(item["b"]["id"], item["a"]["id"], relation=item.get("relation", "uni"), penalty=item.get("penalty", 0.5))

    print("Creation complete, now begin analysis with the critic agent...")
    output, parser = critic.interact(data["id"], parser=parser)
    if not output:
        parser.dump()
        return successful_response({"message": "No changes to be made"}, 200)
    
    # Add new nodes to the parser graph
    for node in output["new_nodes"]:
        parser.graph.add_node(node["id"], label=node.get("label", ""), desc=node.get("desc", ""), graph_id=data["id"])

    # Add new edges to the parser graph
    for edge in output["new_conns"]:
        parser.graph.add_edge(edge.get("a"), edge.get("b"), relation=edge.get("relation", "uni"), penalty=edge.get("penalty", 0.5))
        if edge.get("relation") == "bi":
            parser.graph.add_edge(edge.get("b"), edge.get("a"), relation=edge.get("relation", "uni"), penalty=edge.get("penalty", 0.5))

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
            try:
                g = Graph.query.get(j+1)
                if not g:
                    db.session.add(Graph())
                    db.session.commit()

                if i == 0:
                    print(f"Creating initial nodes for graph {j+1}...")
                    node = Node(graph_id=j+1, label=f"{initial_label} {i}", desc=f"{initial_desc} {i}", is_primary=True)
                    db.session.add(node)
                    db.session.commit()
                data = {"id": j+1, "new_nodes": 3}
                try:
                    output, parser = creative.interact(data["id"], data["new_nodes"])
                except Exception as e:
                    print(f"Error in creative.interact for graph {j+1}: {str(e)}")
                    db.session.rollback()
                    continue
                
                if not output:
                    print(f"Creative agent returned empty output for graph {j+1}")
                    parser.dump()
                    continue
                
                print(f"Creative agent output structure for graph {j+1}: {type(output)} with keys: {output.keys() if isinstance(output, dict) else 'not a dict'}")

                # Add new nodes from agent output to the parser graph
                try:
                    for item in output.get("connections", []):
                        print(f"Processing connection: {item}")
                        # Safely access nested dicts
                        node_a = item.get("a") if isinstance(item, dict) else None
                        node_b = item.get("b") if isinstance(item, dict) else None
                        
                        if node_a is not None and isinstance(node_a, dict) and "id" in node_a:
                            parser.graph.add_node(node_a["id"], label=node_a.get("label", ""), desc=node_a.get("desc", ""), graph_id=data["id"])
                        else:
                            print(f"Warning: Invalid node_a structure: {node_a}")
                        
                        if node_b is not None and isinstance(node_b, dict) and "id" in node_b:
                            parser.graph.add_node(node_b["id"], label=node_b.get("label", ""), desc=node_b.get("desc", ""), graph_id=data["id"])
                        else:
                            print(f"Warning: Invalid node_b structure: {node_b}")
                        
                        if node_a and node_b and "id" in node_a and "id" in node_b:
                            parser.graph.add_edge(node_a["id"], node_b["id"], relation=item.get("relation", "uni"), penalty=item.get("penalty", 0.5), desc=item.get("desc", ""))
                            if item.get("relation") == "bi":
                                parser.graph.add_edge(node_b["id"], node_a["id"], relation=item.get("relation", "uni"), penalty=item.get("penalty", 0.5), desc=item.get("desc", ""))
                except Exception as e:
                    print(f"Error adding connections: {str(e)}")
                    import traceback
                    traceback.print_exc()

                output, parser = critic.interact(data["id"], parser=parser)
                if not output:
                    print("No changes to be made")
                    print(f"GRAPH {j+1} DEVELOPED")
                    parser.dump()
                    continue

                # Add new nodes to the parser graph
                try:
                    for node in output.get("new_nodes", []):
                        if isinstance(node, dict) and "id" in node:
                            parser.graph.add_node(node["id"], label=node.get("label", ""), desc=node.get("desc", ""), graph_id=data["id"])
                        else:
                            print(f"Warning: Invalid node structure from critic: {node}")
                except Exception as e:
                    print(f"Error adding new nodes from critic: {str(e)}")
                    import traceback
                    traceback.print_exc()

                # Add new edges to the parser graph
                try:
                    for edge in output.get("new_conns", []):
                        if edge.get("a") is not None and edge.get("b") is not None:
                            parser.graph.add_edge(edge.get("a"), edge.get("b"), relation=edge.get("relation", "uni"), penalty=edge.get("penalty", 0.5), desc=edge.get("desc", ""))
                            if edge.get("relation") == "bi":
                                parser.graph.add_edge(edge.get("b"), edge.get("a"), relation=edge.get("relation", "uni"), penalty=edge.get("penalty", 0.5), desc=edge.get("desc", ""))
                except Exception as e:
                    print(f"Error adding new edges from critic: {str(e)}")
                    import traceback
                    traceback.print_exc()
                
                # Remove nodes from the parser graph
                try:
                    for node in output.get("nodes_to_delete", []):
                        node_id = node.get("id") if isinstance(node, dict) else node
                        if node_id and node_id in parser.graph:
                            parser.graph.remove_node(node_id)
                except Exception as e:
                    print(f"Error removing nodes: {str(e)}")
                    import traceback
                    traceback.print_exc()
                
                # Remove edges from the parser graph
                try:
                    for edge in output.get("conns_to_delete", []):
                        edge_a = edge.get("a") if isinstance(edge, dict) else edge[0] if isinstance(edge, (list, tuple)) and len(edge) > 0 else None
                        edge_b = edge.get("b") if isinstance(edge, dict) else edge[1] if isinstance(edge, (list, tuple)) and len(edge) > 1 else None
                        if edge_a and edge_b:
                            if parser.graph.has_edge(edge_a, edge_b):
                                parser.graph.remove_edge(edge_a, edge_b)
                            if parser.graph.has_edge(edge_b, edge_a):
                                parser.graph.remove_edge(edge_b, edge_a)
                except Exception as e:
                    print(f"Error removing edges: {str(e)}")
                    import traceback
                    traceback.print_exc()
                
                parser.dump() 
                print(f"GRAPH {j+1} DEVELOPED")
            except Exception as e:
                print(f"Error processing graph {j+1}: {str(e)}")
                db.session.rollback()
                continue
        
        try:
            manager.dump_best()
        except Exception as e:
            print(f"Error in dump_best operation: {str(e)}")
        i += 1
