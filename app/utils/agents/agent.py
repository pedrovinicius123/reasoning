from abc import ABC, abstractmethod
from ...extensions import client, db
from ...schemas.edges_schema import EdgeSchema
from ...schemas.nodes_schema import NodeSchema, Node
from ..networkx_parser import NetworkxParser

class Agent(ABC):
    def __init__(self):
        self.session = db.session
        self.edges_schema = EdgeSchema(many=True)
        self.edge_schema = EdgeSchema()
        self.node_schema = NodeSchema()
        self.client = client
        self.model = "qwen3.5:397b-cloud"

    def prompt_graph(self, graph):
        prompt = "Edges:\n\n"
        for edge in graph.edges():
            a, b = edge
            prompt += f"{a} -> {b}\n"

        prompt += "\nNodes:\n"
        for node in graph.nodes():
            try:
                node_data = graph.nodes[node]
                print(f"Node {node} attributes: {node_data}")
                label = node_data.get('label', '')
                desc = node_data.get('desc', '')
                is_primary = node_data.get('is_primary', False)
                
                prompt += f"{node}:\n"
                prompt += f"Label: {label}\n"
                prompt += f"Description: {desc}\n"
                prompt += f"Is Primary: {is_primary}\n\n"
            except Exception as e:
                print(f"Error accessing node {node} data: {e}")
                print(f"Node data type: {type(graph.nodes[node])}")
                print(f"Node data content: {graph.nodes[node]}")
                raise

        return prompt

    @abstractmethod
    def interact(self, graph_id, parser=None):
        pass