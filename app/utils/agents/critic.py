from .agent import Agent
from ...schemas.agent_schemas import Changes
from ...extensions import client
from ...config import Config
import json

class CriticAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", Config.CRITIC_MODEL)

    def interact(self, graph_id, parser=None):
        if parser is not None:
            self.parser = parser
        else:
            self.build_graph(graph_id)

        prompt = f"""
Analyze the graph bellow and show any issues within the knownledge contained on it.

Propose changes on the nodes and, if necessary, remove nodes, and connections from the knownledge graph.
!IMPORTANT! Do not delete any node marked as primary, and do not propose deletion of any node connected to it.
!IMPORTANT! Return only JSON with the format specified, without any additional text or explanation outside the JSON.
!IMPORTANT! If there are no changes to be made, return an empty JSON ({{}}).

Follow the format bellow strictly (DONT FORGET TO FOLLOW THE FORMAT STRICTLY, ANY DEVIATION FROM THE FORMAT WILL CAUSE PROBLEMS ON THE SYSTEM, SO FOLLOW IT STRICTLY):
{Changes.model_json_schema()}

"""
        prompt += self.prompt_graph()
        response = client.chat(
            model=self.model,
            messages=[{"role":"user", "content": prompt}],
            options = {
                "temperature":.0
            },
            format=Changes.model_json_schema()
        ).message.content
        response = response.replace("json", "")
        response = response.replace("```", "")
        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response from model: {response}") from e
        return result, self.parser
    