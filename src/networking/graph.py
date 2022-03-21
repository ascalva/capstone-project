import csv
import random            as r
import matplotlib.pyplot as plt
import networkx          as nx


class Graph :

    def __init__(self, hostname, filename="topology.csv", random_weights=False) :
        self.host = hostname
        self.g    = nx.Graph()
        self.mst  = nx.Graph()

        self.readGraphFile(filename, random_weights)
        self.computeMST()


    def __getitem__(self, node) :
        return self.mst[node]
    

    def __setitem__(self, node_tuple, weight) :
        node_1, node_2 = node_tuple

        if self.g.has_node(node_1) and self.g.has_node(node_2) :
            self.g.add_weighted_edges_from([(node_1, node_2, weight)])
            self.computeMST()


    def readGraphFile(self, filename, random_weights) :
        random_lb = 1
        random_ub = 20

        with open(filename) as f :
            uncommented = filter(lambda row : row[0] != '#', f)

            for node_1, node_2, weight in csv.reader(uncommented, delimiter=',') :
                if random_weights :
                    weight = r.randint(random_lb, random_ub)
                self.g.add_edge(node_1, node_2, weight=int(weight))


    def computeMST(self, algorithm="kruskal") :
        mst = nx.minimum_spanning_edges(self.g, algorithm)
        self.mst.clear()
        self.mst.update(mst)


    def dropNode(self, node) :
        if self.g.has_node(node) :
            self.g.remove_node(node)
            self.computeMST()
    
    def getNeighbors(self) :
        return list(self[self.host])
    
    def getAllNodes(self) :
        return list(self.g.nodes)


    def visualize(self) :
        val_map = {
            self.host : "#ff0000"
        }
        values = [val_map.get(node, "#1f78b4") for node in self.g.nodes()]
        pos    = nx.spring_layout(self.g, seed=7)

        nx.draw_networkx(self.g, pos, node_color = values)
        nx.draw_networkx_edges(
            self.mst, pos, width=6, alpha=0.3, edge_color="g", style="dashed"
        )

        ax = plt.gca()
        ax.margins(0.08)
        plt.axis("off")
        plt.tight_layout()
        plt.show()

if __name__ == "__main__" :
    g = Graph("A_", random_weights=True)
    g.visualize()