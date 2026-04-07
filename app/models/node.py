from ..extensions import db

class Node(db.Model):
    __tablename__ = 'nodes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_primary = db.Column(db.Boolean, default=False)
    graph_id = db.Column(db.Integer, db.ForeignKey('graph.id'))

    label = db.Column(db.String(128), nullable=False)
    desc = db.Column(db.Text, nullable=False)

    child_edges = db.relationship("Edge", foreign_keys="Edge.parent_id", back_populates="parent")
    parent_edges = db.relationship("Edge", foreign_keys="Edge.child_id", back_populates="child")

from .edges import Edge
