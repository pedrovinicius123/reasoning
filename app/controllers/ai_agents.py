from ..utils.agents.creative import CreativeAgent
from ..utils.agents.critic import CriticAgent
from ..utils.response import successful_response
from ..utils.networkx_parser import NetworkxParserManager
from ..models.graph import Graph
from ..models.node import Node
from ..schemas.edges_schema import EdgeSchema
from ..schemas.nodes_schema import NodeSchema
from ..schemas.agent_request_schemas import JsonRequestAgentSchemaCreative, JsonRequestAgentSchemaCritic
from networkx import DiGraph
from threading import Thread
from flask import request, current_app
import time # for debugging

node_schema = NodeSchema()
edge_schema = EdgeSchema()
req_schema_creative = JsonRequestAgentSchemaCreative()
req_schema_critic = JsonRequestAgentSchemaCritic()

def interact_with_graph(app_instance, task, n_graphs, generations, new_nodes_per_generation):
    with app_instance.app_context():
        
        
        manager = NetworkxParserManager(task=task, n_graphs=n_graphs)
        graph = Graph.query.get(manager.graph_id)
                                
        creative = CreativeAgent(graph_id=graph.id)
        critic = CriticAgent(graph_id=graph.id)

        creative.task = task
        critic.task = task

        for _ in range(generations):
            for i in range(n_graphs):
                results = creative.interact(new_nodes_per_generation)
                for result in results["connections"]:
                    a = result["a"]
                    b = result["b"]

                    creative.graph.add_node(a["id"], **{k: v for k, v in a.items() if k != "id"})                
                    creative.graph.add_node(b["id"], **{k: v for k, v in b.items() if k != "id"})

                    creative.graph.nodes[a["id"]]["graph_id"] = graph.id
                    creative.graph.nodes[b["id"]]["graph_id"] = graph.id

                    creative.graph.add_edge(a["id"], b["id"], **{k: v for k, v in result.items() if k not in ("a", "b")})
                
                reviewed_results = critic.interact()
                if not reviewed_results:
                    manager.parsers[i].graph = creative.graph
                    continue

                for to_add in reviewed_results["new_conns"]:
                    a = to_add["a"]
                    b = to_add["b"]

                    creative.graph.add_node(a["id"], **{k: v for k, v in a.items() if k != "id"})                
                    creative.graph.add_node(b["id"], **{k: v for k, v in b.items() if k != "id"})
                    creative.graph.add_edge(a["id"], b["id"], **{k: v for k, v in to_add.items() if k not in ("a", "b")})

                for rm_node in reviewed_results["nodes_to_delete"]:
                    creative.graph.remove_node(rm_node["id"])

                for rm_conn in reviewed_results["conns_to_delete"]:
                    creative.graph.remove_edge(rm_conn["a"], rm_conn["b"])
                manager.parsers[i].graph = creative.graph.copy()
            manager.dump_best()

def start_interact_with_graph_thread():
    data = request.json
    app_obj_ = current_app._get_current_object()
    print(app_obj_)

    t = Thread(target=interact_with_graph, args=(app_obj_, data["task"], data["n_graphs"], data["generations"], data["new_nodes"]))
    t.start()
    
    return successful_response({"message":"Reasoning thread started!"}, 201)
