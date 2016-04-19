import matsim.network
import matsim.transit
import pickle
import numpy as np
import numpy.linalg as la

"""

"""

import pt_skeleton
skeleton = pt_skeleton.SKELETON

network = matsim.network.Network()
matsim.network.NetworkReader(network).read('network_clean.xml')

class TravelTimeDijkstra(matsim.network.Dijkstra):
    def compute_cost(self, link):
        return link.length / link.freespeed

cache = matsim.network.DijkstraCache(network)
dijkstra = TravelTimeDijkstra(network, cache)

routes = {}

for route_id, skeleton_nodes in skeleton.items():
    nodes = [skeleton_nodes[0]]
    links = []

    for i in range(1, len(skeleton_nodes)):
        result = dijkstra.find_route(skeleton_nodes[i-1], skeleton_nodes[i])
        nodes += result[0][1:]
        links += result[1]

    routes[route_id] = (nodes, links)

with open('routes.dat', 'wb+') as f:
    pickle.dump(routes, f)
