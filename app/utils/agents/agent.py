from ...extensions import client, db
from ...schemas.edges_schema import EdgeSchema
from ...schemas.nodes_schema import NodeSchema, Node
from ..networkx_parser import NetworkxParser

class Agent:
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
        for edge in self.graph.edges():
            a, b = edge
            prompt += f"{a} -> {b}\n"

        prompt = "\nNodes:\n"
        for node in self.graph.nodes():
            n = self.node_schema.load(Node.query.get(node))
            prompt += f"{n}\n"

        return prompt

    def interact(self):
        pass