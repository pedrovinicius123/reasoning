from ..extensions import db



class Graph(db.Model):

    __tablename__ = "graph"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task = db.Column(db.String(256), nullable=False)
    final_essay = db.Column(db.Text, nullable=True)
    edges = db.relationship("Edge", backref="graph", lazy=True)
    nodes = db.relationship("Node", backref="graph", lazy=True)


    reasoning_steps = db.Column(db.JSON, nullable=True)
