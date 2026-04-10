from .agent import Agent
from ...extensions import client
from ...config import Config
from ..networkx_parser import NetworkxParser
import json

class CriticAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", Config.CRITIC_MODEL)

    def interact(self, graph):
        print("Starting critic analysis...")
        prompt = f"""
Analyze the graph bellow and show any issues within the knownledge contained on it.

Propose changes on the nodes and, if necessary, remove nodes, and connections from the knownledge graph.
!IMPORTANT! Do not delete any node marked as primary, and do not propose deletion of any node connected to it.
!IMPORTANT! Return only JSON with the format specified, without any additional text or explanation outside the JSON.
!IMPORTANT! If there are no changes to be made, return an empty JSON ({{}}).
!IMPORTANT! If there are cicles on the graph that involve the primary node, return an empty JSON ({{}}) and do not propose any changes.
!IMPORTANT! Delete only nodes that are inconsistent, not primary, or are not connected to any node.
Follow the format bellow strictly (DONT FORGET TO FOLLOW THE FORMAT STRICTLY, ANY DEVIATION FROM THE FORMAT WILL CAUSE PROBLEMS ON THE SYSTEM, SO FOLLOW IT STRICTLY)
Also, dont forget to left the 'a' and 'b' params of connection in 'int' form but in 'Node' form:
{{
   "new_conns": [{{
    "a": {{
        "id":"integer",
        "label":"string",
        "desc":"string",
        "penalty":"float [0.0 - 1.0]"

    }},
    "b": {{
        "id": "integer",
        "label": "string",
        "desc": "string",
        "penalty":"float [0.0 - 1.0]"
    }},
    "desc": "string",
    "penalty": "float [0.0 - 1.0]",
    "relation": "uni|bi"
    }}],

    "nodes_to_delete":[{{
        "id":"integer",
        "label":"string",
        "desc":"string",
        "penalty":"float [0.0 - 1.0]"

    }}],

    "conns_to_delete":[{{
        "a":"integer",
        "b":"integer",
    }}]
}}

"""
        prompt += self.prompt_graph(graph)
        response = client.chat(
            model=self.model,
            messages=[{"role":"user", "content": prompt}],
            options = {
                "temperature":.0,
            }
        ).message.content
        response = response.replace("json", "")
        response = response.replace("```", "")
        try:
            result = json.loads(response)
            print(result)
            return result
        except json.JSONDecodeError as e:
            print("!!! Invalid JSON response from model:", response)
            raise ValueError(f"Invalid JSON response from model: {response}") from e
        except Exception as e:
            print("!!! Invalid response format:", e)
            raise ValueError(f"Invalid response format: {e}") from e
    