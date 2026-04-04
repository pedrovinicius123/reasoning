from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from ..models.edges import Edge
from marshmallow import fields

class EdgeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Edge
        load_instance = True
        include_fk=True

    penalty = auto_field()
    relation = auto_field()

    # Excluímos o 'parent' para evitar loop ao listar filhos
    parent = fields.Nested("NodeSchema", exclude=("parent_edges", "child_edges"))
    child = fields.Nested("NodeSchema", exclude=("parent_edges", "child_edges"))
