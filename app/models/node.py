from ..extensions import db
from .edges import Edge

class Node(db.Model):
    __tablename__ = 'nodes'
    id = db.Column(db.Integer, primary_key=True)
    graph_id = db.Column(db.Integer, db.ForeignKey('graph.id'))

    label = db.Column(db.String(128), nullable=False)
    desc = db.Column(db.String(1024), nullable=False)

    child_edges = db.relationship("Edge", foreign_keys=[Edge.parent_id], back_populates="parent")
    parent_edges = db.relationship("Edge", foreign_keys=[Edge.child_id], back_populates="child")
