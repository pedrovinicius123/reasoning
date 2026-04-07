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
from networkx import DiGraph
from threading import Thread
from flask import request, current_app

creative = CreativeAgent()
critic = CriticAgent()
node_schema = NodeSchema()
edge_schema = EdgeSchema()
req_schema_creative = JsonRequestAgentSchemaCreative()
req_schema_critic = JsonRequestAgentSchemaCritic()

def interact_with_graph(app_instance, task, n_graphs, generations, new_nodes_per_generation):

    with app_instance.app_context():
        graph = Graph(task=task)
        db.session.add(graph)
        db.session.commit()

        for _ in range(generations):
            manager = NetworkxParserManger()
            for i in range(n_graphs):        
                g = DiGraph()    
                results = creative.interact(g, new_nodes_per_generation)
                for result in results:
                    a = result["a"]
                    b = result["b"]

                    g.add_node(a["id"], **{k: v for k, v in a.items() if k != "id"})                
                    g.add_node(b["id"], **{k: v for k, v in b.items() if k != "id"})
                    g.add_edge(a["id"], b["id"], **{k: v for k, v in result.items() if k not in ("a", "b")})
                
                reviewed_results = critic.interact(g)
                for rev in reviewed_results:
                    for to_add in rev["new_conns"]:
                        a = to_add["a"]
                        b = to_add["b"]

                        g.add_node(a["id"], **{k: v for k, v in a.items() if k != "id"})                
                        g.add_node(b["id"], **{k: v for k, v in b.items() if k != "id"})
                        g.add_edge(a["id"], b["id"], **{k: v for k, v in to_add.items() if k not in ("a", "b")})

                    for rm_node in rev["nodes_to_delete"]:
                        g.remove_node(rm_node["id"])

                    for rm_conn in rev["conns_to_delete"]:
                        g.remove_edge(rm_conn["a"]["id"], rm_conn["b"]["id"])
                manager.parsers[i].graph = g
            manager.dump_best()

def start_interact_with_graph_thread():
    data = request.json
    app_obj_ = current_app._get_current_object()
    print(app_obj_)

    t = Thread(target=interact_with_graph, args=(app_obj_, data["task"], data["n_graphs"], data["generations"], data["new_nodes"]))
    t.start()
    
    return successful_response({"message":"Reasoning thread started!"}, 201)
