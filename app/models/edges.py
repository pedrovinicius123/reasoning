from ..extensions import db
from .graph import Graph

class Edge(db.Model):
    __tablename__ = 'edges'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    graph_id = db.Column(db.Integer, db.ForeignKey('graph.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('nodes.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('nodes.id'), nullable=False)
    
    # Metadado da aresta
    penalty = db.Column(db.Float, nullable=False) 
    relation = db.Column(db.String(100), nullable=False)

    # Relacionamentos para acessar os nós a partir da Edge
    parent = db.relationship("Node", foreign_keys=[parent_id], back_populates="child_edges")
    child = db.relationship("Node", foreign_keys=[child_id], back_populates="parent_edges")

    __table_args__ = (db.UniqueConstraint('graph_id', 'parent_id', 'child_id', name='unique_edge'),)
