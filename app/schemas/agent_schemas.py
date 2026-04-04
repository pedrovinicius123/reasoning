from pydantic import BaseModel, Field
from typing import List, Literal

class Connection(BaseModel):
    a:int
    b:int
    confiability:float = Field(ge=.0, le=1.0)
    relation:Literal['uni', 'bi']

class Node(BaseModel):
    id:int
    label:str
    desc:str
    confiability:float = Field(ge=.0, le=1.0)

class Output(BaseModel):
    conns:List[Connection]

class Changes(BaseModel):
    new_nodes:List[Node]
    new_conns:List[Connection]

    nodes_to_delete:List[Node]
    conns_to_delete:List[Connection]

