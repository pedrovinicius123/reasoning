from ...config import Config
from ...extensions import client
from .agent import Agent

class WriterAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = Config.WRITER_MODEL
        self.essay = ""
    def interact(self, graph):
        # Get the textual representation of the graph
        graph_representation = self.prompt_graph(graph)
        print(graph_representation)
        # Construct the prompt
        prompt = (
            "You are a professional mathematical writer. "
            "Your task is to write a cohesive essay section based on the provided mathematical graph. "
            "The output must be in Markdown format.\n\n"
            f"Current Essay Context:\n{self.essay}\n\n"
            f"Mathematical Graph Representation:\n{graph_representation}\n\n"
            "Please write the next section of the essay, ensuring continuity with the existing context."
        )
        
        # Use ollama.chat with the specified model
        response = client.chat(
            model=self.model,
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )

        print(response)
        return response['message']['content']
