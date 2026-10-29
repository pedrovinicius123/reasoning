from .agent import Agent
from ...config import Config
from ...extensions import client


class WriterAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = kwargs.get("model", Config.WRITER_MODEL)

    def interact(self, graph, on_chunk=None):
        prompt = f"""You are the Writer for a mathematical reasoning system.
Explain the task using only claims and connections present in the graph below.
Distinguish verified facts from unresolved questions. Do not invent proofs or conclusions.
Write concise Markdown. Put inline mathematics in $...$ and displayed equations in $$...$$.
If the graph has no verified connections, say that there is not enough verified evidence.

Task: {self.task}

{self.prompt_graph(graph)}
"""
        response_text = []
        response = client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            options={"temperature": 0.2},
        )
        for part in response:
            text = part.message.content or ""
            response_text.append(text)
            if on_chunk and text:
                on_chunk(text)
        return "".join(response_text)