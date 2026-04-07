from networkx import DiGraph
from ..models.node import Node
from ..schemas.edges_schema import EdgeSchema
from ..models.edges import Edge
from ..models.graph import Graph
from ..extensions import db
from .agents.utils.genetic_crossing_over import crossing_over_and_selection
import networkx as nx
import copy, time



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
    
    def dump(self, to_remove_edges=[], to_remove_nodes=[]):
        try:
            # Merge all nodes from the graph back to the database
            for node_id in self.graph.nodes():
                attrs = self.graph.nodes[node_id]
                node = Node.query.get(node_id)
                if node:
                    node.label = attrs.get("label", "")
                    node.desc = attrs.get("desc", "")
                else:
                    db.session.add(
                        Node(
                            id=node_id,
                            graph_id=self.graph_id,
                            label=attrs.get("label", ""),
                            desc=attrs.get("desc", ""),
                        )
                    )
            
            db.session.commit() # Commit after merging nodes to ensure all nodes have IDs before processing edges
            # Get or create Graph instance
            graph_obj = Graph.query.get(self.graph_id)
            if not graph_obj:
                graph_obj = Graph(id=self.graph_id)
                db.session.add(graph_obj)
            db.session.commit()
            
            # Get the next edge id
            max_edge_id = db.session.query(db.func.max(Edge.id)).scalar() or 0
            
            # Merge all edges from the graph back to the database
            node_ids = list(self.graph.nodes())
            nodes = {node.id: node for node in Node.query.filter(Node.id.in_(node_ids)).all()}
            for parent_id, child_id in self.graph.edges():
                edge_attrs = self.graph[parent_id][child_id]
                parent_node = nodes.get(parent_id)
                child_node = nodes.get(child_id)
                if parent_node and child_node:
                    relation = edge_attrs.get("relation", "uni")
                    penalty = edge_attrs.get("penalty", 0.5)
                    desc = edge_attrs.get("desc", None)
                    
                    edge = Edge.query.filter_by(
                        graph_id=self.graph_id,
                        parent_id=parent_id, 
                        child_id=child_id
                    ).first()
                    
                    if edge:
                        edge.relation = relation
                        edge.penalty = penalty
                        edge.desc = desc
                        db.session.merge(edge)
                    else:
                        max_edge_id += 1
                        new_edge = Edge(
                            graph_id=self.graph_id,
                            parent_id=parent_id,
                            child_id=child_id,
                            relation=relation,
                            penalty=penalty,
                            desc=desc
                        )
                        db.session.add(new_edge)
            
            # Remove marked edges
            for edge_spec in to_remove_edges or []:
                edge_pairs = []
                if isinstance(edge_spec, dict):
                    edge_pairs.append((edge_spec.get("a"), edge_spec.get("b")))
                elif isinstance(edge_spec, (list, tuple)) and len(edge_spec) == 2 and not isinstance(edge_spec[0], (list, tuple)):
                    edge_pairs.append((edge_spec[0], edge_spec[1]))
                else:
                    edge_pairs.extend(
                        (pair[0], pair[1])
                        for pair in edge_spec
                        if isinstance(pair, (list, tuple)) and len(pair) == 2
                    )

                for parent_id, child_id in edge_pairs:
                    if parent_id is None or child_id is None:
                        continue
                    edge = Edge.query.filter_by(
                        graph_id=self.graph_id,
                        parent_id=parent_id,
                        child_id=child_id
                    ).first()
                    if edge:
                        db.session.delete(edge)

            for node_id in to_remove_nodes or []:
                target_id = node_id["id"] if isinstance(node_id, dict) else node_id
                node = Node.query.get(target_id)
                if node:
                    db.session.delete(node)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

class NetworkxParserManger:
    def __init__(self, n_graphs):
        graph = Graph.query.order_by(Graph.id.desc()).first()
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
        self.best = NetworkxParser(graph_id=1)
        self.best.graph = bst
        self.best.dump()  # Persist the best graph to graph_id=1 only
    