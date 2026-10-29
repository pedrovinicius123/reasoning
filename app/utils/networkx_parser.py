from networkx import DiGraph
from ..models.node import Node
from ..schemas.edges_schema import EdgeSchema
from ..models.edges import Edge
from ..models.graph import Graph
from ..extensions import db
from .agents.agent_utils.genetic_crossing_over import crossing_over_and_selection
import copy
import re
import unicodedata


def normalize_node_label(label):
    if not isinstance(label, str):
        return ""
    label = unicodedata.normalize("NFKC", label)
    for command, symbol in (
        ("leftrightarrow", "↔"),
        ("implies", "→"),
        ("subseteq", "⊆"),
        ("notin", "∉"),
        ("neq", "≠"),
        ("ne", "≠"),
        ("land", "∧"),
        ("lor", "∨"),
        ("to", "→"),
        ("in", "∈"),
    ):
        label = re.sub(rf"\\{command}\b", symbol, label)
    label = label.replace("!=", "≠").replace("\\", "∖")
    label = re.sub(r"\s*([=≠<>≤≥∈∉⊆⊂∧∨→↔∖])\s*", r"\1", label)
    return " ".join(label.split())


def collapse_duplicate_nodes(graph):
    collapsed = DiGraph()
    canonical_ids = {}
    id_map = {}

    for node_id, attributes in graph.nodes(data=True):
        label_key = normalize_node_label(attributes.get("label", ""))
        canonical_id = canonical_ids.get(label_key) if label_key else None
        if canonical_id is None:
            canonical_id = node_id
            if label_key:
                canonical_ids[label_key] = canonical_id
            collapsed.add_node(canonical_id, **attributes.copy())
        else:
            canonical = collapsed.nodes[canonical_id]
            canonical["is_primary"] = canonical.get("is_primary", False) or attributes.get("is_primary", False)
            if len(attributes.get("desc", "")) > len(canonical.get("desc", "")):
                canonical["desc"] = attributes["desc"]
        id_map[node_id] = canonical_id

    for source, target, attributes in graph.edges(data=True):
        canonical_source = id_map[source]
        canonical_target = id_map[target]
        if canonical_source == canonical_target:
            continue
        if not collapsed.has_edge(canonical_source, canonical_target):
            collapsed.add_edge(canonical_source, canonical_target, **attributes.copy())
            continue

        canonical_edge = collapsed.edges[canonical_source, canonical_target]
        if attributes.get("relation") == "bi":
            canonical_edge["relation"] = "bi"
        if attributes.get("penalty", float("inf")) < canonical_edge.get("penalty", float("inf")):
            canonical_edge["penalty"] = attributes["penalty"]
        if len(attributes.get("desc") or "") > len(canonical_edge.get("desc") or ""):
            canonical_edge["desc"] = attributes["desc"]

    return collapsed


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
        self.graph = DiGraph()
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
        self.graph = collapse_duplicate_nodes(self.graph)
        node_ids = {}
        for node_id in self.graph.nodes:
            node_data = self.graph.nodes[node_id]
            node = Node.query.filter_by(id=node_id, graph_id=self.graph_id).first()

            if node:
                for k, v in node_data.items():
                    if hasattr(node, k):
                        setattr(node, k, v)
            else:
                node = Node(
                    graph_id=self.graph_id,
                    label=node_data.get("label", ""),
                    desc=node_data.get("desc", ""),
                    is_primary=node_data.get("is_primary", False),
                )
                db.session.add(node)
                db.session.flush()
            node_ids[node_id] = node.id

        persisted_node_ids = {
            node_id
            for (node_id,) in db.session.query(Node.id).filter_by(graph_id=self.graph_id).all()
        }
        stale_node_ids = persisted_node_ids - set(node_ids.values())
        if stale_node_ids:
            Edge.query.filter_by(graph_id=self.graph_id).filter(
                Edge.parent_id.in_(stale_node_ids)
            ).delete(synchronize_session=False)
            Edge.query.filter_by(graph_id=self.graph_id).filter(
                Edge.child_id.in_(stale_node_ids)
            ).delete(synchronize_session=False)
            Node.query.filter_by(graph_id=self.graph_id).filter(
                Node.id.in_(stale_node_ids)
            ).delete(synchronize_session=False)

        for edge in self.graph.edges(data=True):
            source_id, target_id, edge_data = edge
            if (source_id, target_id) in to_remove_edges:
                continue
            parent_id = node_ids[source_id]
            child_id = node_ids[target_id]

            edge_record = Edge.query.filter_by(
                graph_id=self.graph_id, parent_id=parent_id, child_id=child_id
            ).first()
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
        graph = Graph(task=task)
        db.session.add(graph)
        db.session.commit()

        self.graph_id = graph.id
        self.best = None
        self.parsers = []
        for _ in range(n_graphs):
            graph, parser = NetworkxParser(self.graph_id).load()
            self.parsers.append(parser)
            print(self.parsers, graph)
        self.best = self.parsers[-1]
    
    def set_parser_graph(self, index:int, graph):
        self.parsers[index].graph = graph

    def dump_best(self):
        graphs_with_edges = [copy.deepcopy(parser.graph) for parser in self.parsers if parser.graph.edges()]
        if not graphs_with_edges:
            graphs_with_nodes = [copy.deepcopy(parser.graph) for parser in self.parsers if parser.graph.nodes()]
            if not graphs_with_nodes:
                return self.parsers[0].graph
            bst = graphs_with_nodes[0]
        elif len(graphs_with_edges) == 1:
            bst = graphs_with_edges[0]
        else:
            bst = crossing_over_and_selection(*graphs_with_edges)
        self.best = NetworkxParser(self.graph_id)
        self.best.graph = bst
        self.best.dump()
        self.best.load()
        for parser in self.parsers:
            parser.graph = copy.deepcopy(self.best.graph)

        return self.best.graph