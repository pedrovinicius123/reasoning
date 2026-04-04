from itertools import combinations
from networkx import DiGraph

def edges_mean(graph):
    return sum([edge["confiability"] for edge in graph.edges()])/len(graph.edges())

def crossing_over_and_selection(*graphs, threshold=.6):
    pairs = combinations(graphs)
    new_gs = []

    for a, b in pairs:
        best_edges_a = [edge for edge in a.edges() if edge["confiability"] >= threshold]
        best_edges_b = [edge for edge in b.edges() if edge["confiability"] >= threshold]
        
        g = DiGraph()
        g.add_edges_from(best_edges_a + best_edges_b)
        new_gs.append(g)

    best_g = max(new_gs, key=edges_mean)
    return best_g                        
