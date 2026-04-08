from app import create_app
from app.utils.networkx_parser import NetworkxParserManger
from networkx import DiGraph
import random

app = create_app()
if __name__ == "__main__":
    # TESTING!
    def generate_random_dummy_graphs(n_nodes:int, conn_prob:float):
        g = DiGraph()
        for i in range(n_nodes):
            for j in range(n_nodes):
                if i != j and random.random() > 1-conn_prob:
                    g.add_edge(i, j)
                    g[i]["label"] = "label"
                    g[j]["label"] = "label"
                    g[i][j]["penalty"] = random.random()

        return g


    with app.app_context():
        manager = NetworkxParserManger("Solve p vs np", 2)
        
        for parser in manager.parsers:
            parser.graph = generate_random_dummy_graphs(20, .5)
        manager.dump_best()
