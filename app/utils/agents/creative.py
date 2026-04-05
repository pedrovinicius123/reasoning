from .agent import Agent
from ...schemas.agent_schemas import Output
from ...extensions import client
import json

class CreativeAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", "qwen3.5:397b-cloud")

    def interact(self, graph_id, new_nodes):
        prompt = f"""
Propose {new_nodes} new nodes for this graph, with its's respective labels, descriptions and conbfiabilities
in order to append new knownledge for this graph. Also, for each new node, propose connections with the existing nodes in the graph, with a label, description and confiability for each connection.

*Note*: the relations can be implications ("uni") or equities ("bi")

!IMPORTANT! Return only JSON with the format specified, without any additional text or explanation outside the JSON.
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
        results = json.loads(response)
        return results, self.parser
