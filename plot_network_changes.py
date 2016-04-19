import matsim.network
import matsim.facilities
import matplotlib.pyplot as plt
import pickle

class Plotter(matsim.network.NetworkPlotter):
    def __init__(self, transformed, shrunk, moved, removed, loose, detached, duplicates):
        matsim.network.NetworkPlotter.__init__(self, transformed)
        self.shrunk = shrunk
        self.moved = moved
        self.removed = removed
        self.loose = loose
        self.detached = detached
        self.duplicates = duplicates

    def get_link_style(self, link):
        if link.id in self.moved:
            return { 'color' : 'b', 'alpha' : 0.25, 'linestyle' : ':' }
        elif link.id in self.removed:
            return { 'color' : 'r' }
        elif link.id in self.loose or link.id in self.detached or link.id in self.duplicates:
            return { 'color' : 'g' }
        else:
            return { 'color' : 'k' }

    def plot_link(self, link, start, end):
        if link.id in self.moved:
            moved_link = self.shrunk.links[link.id]
            moved_start = self.shrunk.nodes[moved_link.from_node_id].coords
            moved_end = self.shrunk.nodes[moved_link.to_node_id].coords

            matsim.network.NetworkPlotter.plot_link(self, moved_link, moved_start, moved_end, style = { 'color' : 'b' })

        matsim.network.NetworkPlotter.plot_link(self, link, start, end)

transformed = matsim.network.Network()
matsim.network.NetworkReader(transformed).read('network_transformed.xml')

shrunk = matsim.network.Network()
matsim.network.NetworkReader(shrunk).read('network_shrunk.xml')

with open('network_shrunk.dat', 'rb') as f:
    removed, moved = pickle.load(f)[:2]

with open('network_clean.dat', 'rb') as f:
    data = pickle.load(f)
    loose, detached, duplicates = data[1], data[3], data[4]

plotter = Plotter(transformed, shrunk, moved, removed, loose, detached, duplicates)

plt.figure(figsize=(12, 12))
plotter.plot()

plt.axis('off')
plt.savefig('network.pdf')
