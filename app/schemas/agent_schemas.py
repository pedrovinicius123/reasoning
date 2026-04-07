from pydantic import BaseModel, Field
from typing import List, Literal, Tuple

class Connection(BaseModel):
    a: "Node"
    b: "Node"
    desc: str
    penalty: float = Field(ge=.0, le=1.0)
    relation: Literal['uni', 'bi']

class Node(BaseModel):
    id:int
    label:str
    desc:str
    penalty:float = Field(ge=.0, le=1.0)
    conns:List[Connection]

class Output(BaseModel):
    connections:List[Connection]

class Changes(BaseModel):
    new_conns:List[Connection]

    nodes_to_delete:List[Node]
    conns_to_delete:List[Connection]

