from .agent import Agent
from ...extensions import client
from ...config import Config
from ...models.graph import Graph
from ..networkx_parser import NetworkxParser
import json

class CreativeAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", Config.CREATIVE_MODEL)

    def interact(self, new_nodes, graph):
        prompt = f"""
Propose {new_nodes} new nodes for this graph, with its's respective labels, descriptions and penalties, in order to fullfill the assigned task bellow
in order to append new mathematical knowledge for this graph. Also, for each new node, propose connections with the existing nodes in the graph, with a label, description and confiability for each connection.
For each connection, describe the mathematical relation between the nodes, if there is any, and how the new node affects the existing node and vice versa.

*Note*: the relations can be implications ("uni") or equities ("bi")
!TASK! {self.task}

!IMPORTANT! DO NOT USE CONJECTURES, ONLY WELL STABILISHED THEOREMS AND LEMMAS
!IMPORTANT! If there are no nodes or edges present on the graph, create {new_nodes} new ones, with its connections. 
!IMPORTANT! RETURN ONLY JSON with the format specified, without any additional text or explanation outside the JSON.
!IMPORTANT! Only use estabilished concepts on the graph, dont create new concepts that are not connected to any existing node, all new nodes must be connected to at least one existing node, and the connections must make sense with the knownledge already present on the graph, so use the existing nodes as reference for creating new nodes and connections.
!IMPORTANT! Write the response clearly and extensivelly!
!IMPORTANT! If there are cicles on the graph that involve the primary node, return an empty JSON ({{}}) and do not propose any changes.

Follow the format bellow strictly (DONT FORGET TO FOLLOW THE FORMAT STRICTLY, ANY DEVIATION FROM THE FORMAT WILL CAUSE PROBLEMS ON THE SYSTEM, SO FOLLOW IT STRICTLY):
{{
    "connections": [{{
        "a": {{
            "id": "integer",
            "label": "string",
            "desc": "string",
            "penalty": "float [0.0 - 1.0]"
        }},
        "b": {{
            "id": "integer",
            "label": "string",
            "desc": "string",
            "penalty": "float [0.0 - 1.0]"
        }},
        "desc": "string",
        "penalty": "float [0.0 - 1.0]",
        "relation": "string [uni|bi]"
    }}]
}}

"""
        
        print("Before bug")
        prompt += self.prompt_graph(graph)
        print("Prompt built, sending to model...")
        response = client.chat(
            model=self.model,
            messages=[{"role":"user", "content":prompt}],
            options = {
                "temperature":.5,
            }
        ).message.content
        response = response.replace("```json", "").replace("```", "")
        print(response)
        try:
            results = json.loads(response)
            print(results)
            # Validate against schema
            return results
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from model: {response}") from e
        except Exception as e:
            raise ValueError(f"Invalid response format: {e}") from e
