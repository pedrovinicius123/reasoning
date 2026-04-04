from marshmallow_sqlalchemy import auto_field, SQLAlchemyAutoSchema
from marshmallow.validate import Length
from marshmallow import fields
from ..models.node import Node
from ..extensions import db


class NodeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Node
        load_instance = True
        sqla_session = db.session
        include_fk=True

    id = auto_field(dump_only=True)
    label=auto_field(validate=Length(min=16, max=255))
    desc=auto_field(validate=Length(min=128, max=1024))

    # Para evitar recursão infinita na serialização, costuma-se mostrar apenas um nível
    child_edges = fields.Nested("EdgeSchema", many=True)
    parent_edges = fields.Nested("EdgeSchema", many=True)
