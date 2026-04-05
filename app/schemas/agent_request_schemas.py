from ..extensions import m
from marshmallow import fields

class JsonRequestAgentSchemaCreative(m.Schema):
    id=fields.Int(required=True)
    new_nodes=fields.Int(required=True)


class JsonRequestAgentSchemaCritic(m.Schema):
    id=fields.Int(required=True)
