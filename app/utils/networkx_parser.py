from networkx import DiGraph
from ..models.node import Node
from ..schemas.edges_schema import Edge, EdgeSchema
from ..models.graph import Graph
from ..extensions import db
import networkx as nx


class NetworkxParser:
    def __init__(self, graph_id):
        self.graph = DiGraph()
        self.graph_id = graph_id
        self.edges_schema = EdgeSchema(many=True)

    def load(self):
        code_json = self.edges_schema.dump(Edge.query.filter_by(graph_id=self.graph_id))
        for item in code_json:
            a, b = item["parent"], item["child"]
            self.graph.add_edge(a["id"], b["id"])

            if item["relation"] == "bi":
                self.graph.add_edge(b["id"], a["id"])

            nx.set_node_attributes(self.graph, {a["id"]: {k: v for k, v in a.items()if k != "id"}})
            nx.set_node_attributes(self.graph, {b["id"]: {k: v for k, v in b.items()if k != "id"}})

        return self.graph
    
    def dump(self, to_remove):
        for node in self.graph.nodes():
            db.session.add(Node(**node))
        for n in self.graph.nodes():
            node = Node.query.get(n)
            for neighbor in self.graph.neighbors(n):
                ne = Node.query.get(neighbor)                
                edge = Edge(parent=node, child=ne, relation="uni" if n not in self.graph.neighbors(neighbor) else "bi", **self.graph[n][neighbor])
                
                if frozenset([node, ne]) in to_remove:
                    db.session.delete(edge)

                elif not Edge.query.filter_by(parent=node, child=ne, relation=edge.relation).first():
                    g = Graph.query.get(self.graph_id)
                    edge.graph = g           
                

        db.session.commit()
