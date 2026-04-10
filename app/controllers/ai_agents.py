from ..utils.agents.creative import CreativeAgent
from ..utils.agents.critic import CriticAgent
from ..utils.response import successful_response
from ..utils.networkx_parser import NetworkxParserManager, NetworkxParser
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
        graph, _ = NetworkxParser(graph_id=manager.graph_id).load()
        
        creative = CreativeAgent()
        critic = CriticAgent()

        creative.task = task
        critic.task = task

        for _ in range(generations):
            for i in range(n_graphs):
                parsing = graph.copy()
                results = creative.interact(new_nodes_per_generation, graph=graph)
                for result in results["connections"]:
                    a = result["a"]
                    b = result["b"]

                    parsing.add_node(a["id"], **{k: v for k, v in a.items() if k != "id"})                
                    parsing.add_node(b["id"], **{k: v for k, v in b.items() if k != "id"})

                    parsing.nodes[a["id"]]["graph_id"] = manager.graph_id
                    parsing.nodes[b["id"]]["graph_id"] = manager.graph_id

                    parsing.add_edge(a["id"], b["id"], **{k: v for k, v in result.items() if k not in ("a", "b")})
                
                reviewed_results = critic.interact(graph=parsing)
                if not reviewed_results:
                    manager.parsers[i].graph = parsing
                    continue

                for to_add in reviewed_results["new_conns"]:
                    a = to_add["a"]
                    b = to_add["b"]

                    parsing.add_node(a["id"], **{k: v for k, v in a.items() if k != "id"})                
                    parsing.add_node(b["id"], **{k: v for k, v in b.items() if k != "id"})
                    parsing.add_edge(a["id"], b["id"], **{k: v for k, v in to_add.items() if k not in ("a", "b")})

                for rm_node in reviewed_results["nodes_to_delete"]:
                    parsing.remove_node(rm_node["id"])

                for rm_conn in reviewed_results["conns_to_delete"]:
                    parsing.remove_edge(rm_conn["a"], rm_conn["b"])
                manager.parsers[i].graph = parsing.copy()
            graph = manager.dump_best()

def start_interact_with_graph_thread():
    data = request.json
    app_obj_ = current_app._get_current_object()
    print(app_obj_)

    t = Thread(target=interact_with_graph, args=(app_obj_, data["task"], data["n_graphs"], data["generations"], data["new_nodes"]))
    t.start()
    
    return successful_response({"message":"Reasoning thread started!"}, 201)
