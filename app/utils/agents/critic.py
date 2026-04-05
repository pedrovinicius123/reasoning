from .agent import Agent
from ...schemas.agent_schemas import Changes
from ...extensions import client

class CriticAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", "gemma4:e4b")

    def interact(self, graph_id):
        prompt = f"""
Analyze the graph bellow and show any issues within the knownledge contained on it.
Propose changes on the nodes and, if necessary, remove nodes, and connections from the knownledge graph.
!IMPORTANT! Return only JSON with the format specified, without any additional text or explanation outside the JSON.

Follow the format bellow strictly:
{Changes.model_json_schema()}

"""
        self.build_graph(graph_id)
        prompt += self.prompt_graph()
        response = Changes.model_validate_json(client.chat(
            model=self.model,
            messages=[{"role":"user", "content": prompt}],
            options = {
                "temperature":.0
            }
        ).message.content)
        return response, self.parser
    