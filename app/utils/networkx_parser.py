from networkx import DiGraph
from ..models.node import Node
from ..extensions import db

class NetworkxParser:
    def __init__(self):
        self.graph = DiGraph()

    def load(self, *code_json):
        for item in code_json:
            for child in item["children"]:
                self.graph.add_edge(item["id"], child["id"], penalty=.5)

        return self.graph
    
    def dump(self, graph):
        self.graph = graph
        for n in self.graph.nodes():
            node = Node.query.get(n)
            for neighbor in self.graph.neighbors(n):
                ne = Node.query.get(neighbor)
                ne.parents.append(node)

        db.session.commit()
