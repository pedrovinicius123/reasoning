from networkx import DiGraph
from ..models.node import Node
from ..schemas.edges_schema import EdgeSchema
from ..models.edges import Edge
from ..models.graph import Graph
from ..extensions import db
import networkx as nx


class NetworkxParser:
    def __init__(self, graph_id):
        self.graph = DiGraph()
        self.graph_id = graph_id
        self.edges_schema = EdgeSchema(many=True)
        self.edge_schema = EdgeSchema()

    def _node_attrs(self, node):
        return {
            "graph_id": node.graph_id,
            "label": node.label,
            "desc": node.desc,
        }

    def load(self):
        nodes = Node.query.filter_by(graph_id=self.graph_id).all()
        for item in nodes:
            self.graph.add_node(item.id, **self._node_attrs(item))

            for ep in item.parent_edges:
                a, b = ep.parent, ep.child
                self.graph.add_edge(a.id, b.id, relation=ep.relation, penalty=ep.penalty)
                if ep.relation == "bi":
                    self.graph.add_edge(b.id, a.id, relation=ep.relation, penalty=ep.penalty)

                nx.set_node_attributes(self.graph, {a.id: self._node_attrs(a)})

            for ec in item.child_edges:
                a, b = ec.parent, ec.child
                self.graph.add_edge(a.id, b.id, relation=ec.relation, penalty=ec.penalty)
                if ec.relation == "bi":
                    self.graph.add_edge(b.id, a.id, relation=ec.relation, penalty=ec.penalty)

                nx.set_node_attributes(self.graph, {b.id: self._node_attrs(b)})

        return self.graph
    
    def dump(self, to_remove):
        # Merge all nodes from the graph back to the database
        for node_id in self.graph.nodes():
            attrs = self.graph.nodes[node_id]
            db.session.merge(
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
        for parent_id, child_id in self.graph.edges():
            edge_attrs = self.graph[parent_id][child_id]
            parent_node = Node.query.get(parent_id)
            child_node = Node.query.get(child_id)
            
            if parent_node and child_node:
                relation = edge_attrs.get("relation", "uni")
                penalty = edge_attrs.get("penalty", 0.5)
                
                edge = Edge.query.filter_by(
                    graph_id=self.graph_id,
                    parent_id=parent_id, 
                    child_id=child_id
                ).first()
                
                if edge:
                    edge.relation = relation
                    edge.penalty = penalty
                    db.session.merge(edge)
                else:
                    max_edge_id += 1
                    new_edge = Edge(
                        id=max_edge_id,
                        graph_id=self.graph_id,
                        parent_id=parent_id,
                        child_id=child_id,
                        relation=relation,
                        penalty=penalty
                    )
                    db.session.add(new_edge)
        
        # Remove marked edges
        for edge_pair in to_remove:
            for node_pair in edge_pair:
                edge = Edge.query.filter_by(
                    graph_id=self.graph_id,
                    parent_id=node_pair[0],
                    child_id=node_pair[1]
                ).first()
                if edge:
                    db.session.delete(edge)
        
        db.session.commit()

