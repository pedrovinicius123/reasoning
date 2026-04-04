from ..extensions import m
from marshmallow import fields

class JsonRequestAgentSchemaCreative(m.Schema):
    id=fields.Int(required=True)
    relation=fields.Str(required=True)


class JsonRequestAgentSchemaCritic(m.Schema):
    id=fields.Int(required=True)
