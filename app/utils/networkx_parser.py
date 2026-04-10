from networkx import DiGraph
from ..models.node import Node
from ..schemas.edges_schema import EdgeSchema
from ..models.edges import Edge
from ..models.graph import Graph
from ..extensions import db
from .agents.agent_utils.genetic_crossing_over import crossing_over_and_selection
import copy


class NetworkxParser:
    def __init__(self, graph_id):
        self.graph = DiGraph()
        self.graph_id = graph_id
        self.edges_schema = EdgeSchema(many=True)
        self.edge_schema = EdgeSchema()

    def _node_attrs(self, node):
        try:
            attrs = {
                "graph_id": node.graph_id,
                "label": node.label if node.label else "",
                "desc": node.desc if node.desc else "",
                "is_primary": getattr(node, 'is_primary', False),
            }
            return attrs
        except AttributeError as e:
            print(f"Error extracting attributes from node {node.id}: {e}")
            print(f"Node object: {node}")
            print(f"Node dir: {[attr for attr in dir(node) if not attr.startswith('_')]}")
            raise

    def load(self):
        nodes = Node.query.filter_by(graph_id=self.graph_id).all()
        for item in nodes:
            self.graph.add_node(item.id, **self._node_attrs(item))

        edges = Edge.query.filter_by(graph_id=self.graph_id).all()
        for ep in edges:
            self.graph.add_edge(ep.parent_id, ep.child_id, relation=ep.relation, penalty=ep.penalty, desc=ep.desc)
            if ep.relation == "bi" and not self.graph.has_edge(ep.child_id, ep.parent_id):
                self.graph.add_edge(ep.child_id, ep.parent_id, relation=ep.relation, penalty=ep.penalty, desc=ep.desc)

        return self.graph, self
    
    def dump(self, to_remove_edges=[]):
        for node_id in self.graph.nodes:
            node_data = self.graph.nodes[node_id]
            print(node_data)
            node = Node.query.filter_by(id=node_id).first()

            if node:
                for k, v in node_data.items():
                    setattr(node, k, v)
            else:
                # Filter to valid Node attributes
                valid_keys = {'graph_id', 'label', 'desc', 'is_primary'}
                filtered_data = {k: v for k, v in node_data.items() if k in valid_keys}
                print("FILTERED ", filtered_data)
                node = Node(**filtered_data)
                db.session.add(node)

        for edge in self.graph.edges(data=True):
            parent_id, child_id, edge_data = edge
            if (parent_id, child_id) in to_remove_edges:
                continue

            edge_record = Edge.query.filter_by(parent_id=parent_id, child_id=child_id).first()
            if edge_record:
                for k, v in edge_data.items():
                    if hasattr(edge_record, k):
                        setattr(edge_record, k, v)
            else:
                valid_keys = {'relation', 'penalty', 'desc'}
                filtered_data = {k: v for k, v in edge_data.items() if k in valid_keys}
                new_edge = Edge(parent_id=parent_id, child_id=child_id, graph_id=self.graph_id, **filtered_data)
                db.session.add(new_edge)       

        db.session.commit()


class NetworkxParserManager:
    def __init__(self, task, n_graphs):
        graph = Graph.query.order_by(Graph.id.desc()).first()
        if not graph:
            graph = Graph(task=task)
            db.session.add(graph)
            db.session.commit()

        self.graph_id = graph.id
        self.best = None
        self.parsers = []
        for _ in range(n_graphs):
            _, parser = NetworkxParser(self.graph_id).load()
            self.parsers.append(parser)
        self.best = self.parsers[-1]

    def dump_best(self):
        graphs_with_edges = [copy.deepcopy(parser.graph) for parser in self.parsers if parser.graph.edges()]
        if not graphs_with_edges:
            return  # No graphs with edges to process
        bst = crossing_over_and_selection(*graphs_with_edges)
        self.best = NetworkxParser(self.graph_id)
        self.best.graph = bst
        self.best.dump()  # Persist the best graph to graph_id=1 only
        return bst