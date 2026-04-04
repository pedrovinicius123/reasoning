from .agent import Agent
from ...schemas.agent_schemas import Output
from ...extensions import client

class CreativeAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", "qwen3.5:397b-cloud")

    def interact(self, graph_id, new_nodes):
        prompt = f"""
Propose {new_nodes} new nodes for this graph, with its's respective labels, descriptions and conbfiabilities
in order to append new knownledge for this graph (

*Note*: the relations can be implications ("uni") or equities ("bi")

"""
        self.build_graph(graph_id)
        prompt += self.prompt_graph()
        response = Output.model_validate_json(client.chat(
            model=self.model,
            messages=[{"role":"user", "content": prompt}],
            format=Output.model_json_schema(),
            options = {
                "temperature":.5
            }
        ).message.content)
        return response, self.parser
