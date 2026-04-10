from app import create_app
from app.utils.networkx_parser import NetworkxParser
from networkx import DiGraph
from app.utils.agents.creative import CreativeAgent
import random

app = create_app()
if __name__ == "__main__":
    # TESTING!
    with app.app_context():
        graph, _ = NetworkxParser(graph_id=1).load()
        creative_agent = CreativeAgent()
        result = creative_agent.prompt_graph(graph)
        print(result)
