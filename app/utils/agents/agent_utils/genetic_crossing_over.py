from itertools import combinations
from networkx import DiGraph

def edges_mean(graph):
    if not graph.edges():
        return 0
    return sum([edge[2]["penalty"] for edge in graph.edges(data=True)])/len(graph.edges())

def crossing_over_and_selection(*graphs, threshold=.1):
    pairs = combinations(graphs, 2)
    new_gs = []

    for a, b in pairs:
        print(a.edges(data=True), b.edges(data=True))
        best_edges_a = [edge for edge in a.edges(data=True) if edge[2]["penalty"] <= threshold]
        best_edges_b = [edge for edge in b.edges(data=True) if edge[2]["penalty"] <= threshold]

        print(best_edges_a, best_edges_b)
        
        g = DiGraph()
        g.add_edges_from(best_edges_a + best_edges_b)
        
        # Copy node attributes
        for node in g.nodes():
            if not g.neighbors(node):
                g.remove_node(node)
                continue
            
            if node in a.nodes():
                g.nodes[node].update(a.nodes[node])
            if node in b.nodes:
                g.nodes[node].update(b.nodes[node])
        
        new_gs.append(g)

    best_g = max(new_gs, key=edges_mean)
    return best_g                        
