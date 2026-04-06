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

    def build_graph(self, graph_id:int):
        self.parser = NetworkxParser(graph_id)
        self.parser.load()

    def prompt_graph(self):
        prompt = "Edges:\n\n"
        for edge in self.parser.graph.edges():
            a, b = edge
            prompt += f"{a} -> {b}\n"

        prompt += "\nNodes:\n"
        for node in self.parser.graph.nodes():
            prompt += f"{node}:\n"
            prompt += f"Label: {self.parser.graph.nodes[node]['label']}\n"
            prompt += f"Description: {self.parser.graph.nodes[node]['desc']}\n"
            prompt += f"Is Primary: {self.parser.graph.nodes[node].get('is_primary', False)}\n\n"

        return prompt

    @abstractmethod
    def interact(self, graph_id, parser=None):
        pass