import matsim.network

network = matsim.network.Network()
matsim.network.NetworkReader(network).read('network_clean.xml')

class TravelTimeDijkstra(matsim.network.Dijkstra):
    def calculate_cost(self, link):
        return link.length / link.freespeed;

dijkstra = TravelTimeDijkstra(network)
route, cost = dijkstra.find_route('80654707', '2450178871')

print(route, cost)
