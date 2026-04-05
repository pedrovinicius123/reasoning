from ..extensions import db

class Graph(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    edges = db.relationship("Edge", backref="graph",lazy=True)
    nodes = db.relationship("Node", backref="graph",lazy=True)
