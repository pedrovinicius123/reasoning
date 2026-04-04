from ..utils.agents.creative import CreativeAgent
from ..utils.agents.critic import CriticAgent
from ..utils.response import successful_response
from ..schemas.agent_request_schemas import JsonRequestAgentSchemaCreative, JsonRequestAgentSchemaCritic
from flask import request
import networkx as nx

creative = CreativeAgent()
critic = CriticAgent()
req_schema_creative = JsonRequestAgentSchemaCreative()
req_schema_critic = JsonRequestAgentSchemaCritic()

def interact_with_graph():
    data = req_schema_creative.load(request.get_json())
    output, parser = creative.interact(data["id"], data["new_nodes"])

    for item in output.nodes:
        for neighbor in item.conn:
            parser.graph.add_edge(item.node, neighbor, label=item.label, desc=item.desc)

    parser.dump()
    return successful_response(output, 201)

def analyse_graph():
    data = req_schema_critic.load(request.get_json())
    output, parser = critic.interact(data["id"])
    for node in output.new_nodes:
        if node.id not in parser.graph:
            parser.graph.add_node(node.id)

        attrs = {node.id: {k: v for k, v in node.__dict__().items() if k != "id"}}
        nx.set_node_attributes(parser.graph, attrs)

    for edge in output.new_edges:
        if (edge.a, edge.b) not in parser.graph.edges():
            parser.graph.add_edge(edge.a, edge.b, confiability=edge.confiability, relation=edge.relation)
        else:
            parser.graph[edge.a][edge.b].update({
                "confiability": edge.confiability,
                "relation": edge.relation
            })

    for rm_node in output.nodes_to_delete:
        parser.graph.pop(rm_node)

    for rm_edge in output.conns_to_delete:
        parser.graph.remove_edge(rm_edge.a, rm_edge.b)
    parser.dump()
    return successful_response(output)
