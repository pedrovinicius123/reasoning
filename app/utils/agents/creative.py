from .agent import Agent
from ...schemas.agent_schemas import Output
from ...extensions import client
from ...config import Config
import json

class CreativeAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", Config.CREATIVE_MODEL)

    def interact(self, graph_id, new_nodes):
        prompt = f"""
Propose {new_nodes} new nodes for this graph, assuming everything on it is True, with its's respective labels, descriptions and penalties
in order to append new knownledge for this graph. Also, for each new node, propose connections with the existing nodes in the graph, with a label, description and confiability for each connection.

*Note*: the relations can be implications ("uni") or equities ("bi")

!IMPORTANT! Return only JSON with the format specified, without any additional text or explanation outside the JSON.
!IMPORTANT! Only use estabilished concepts on the graph, dont create new concepts that are not connected to any existing node, all new nodes must be connected to at least one existing node, and the connections must make sense with the knownledge already present on the graph, so use the existing nodes as reference for creating new nodes and connections.
Write the response clearly and extensivelly!


Follow the format bellow strictly (DONT FORGET TO FOLLOW THE FORMAT STRICTLY, ANY DEVIATION FROM THE FORMAT WILL CAUSE PROBLEMS ON THE SYSTEM, SO FOLLOW IT STRICTLY):
{Output.model_json_schema()}
"""
        self.build_graph(graph_id)
        prompt += self.prompt_graph()
        response = client.chat(
            model=self.model,
            messages=[{"role":"user", "content": prompt}],
            options = {
                "temperature":.5
            }
        ).message.content
        response = response.replace("```json", "").replace("```", "")
        try:
            results = json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from model: {response}") from e
        return results, self.parser
