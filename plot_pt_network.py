import matsim.network
import matsim.transit
import matplotlib.pyplot as plt
import pickle

def get_skeleton_nodes():
    import pt_skeleton

    skeleton_nodes = []
    for nodes in pt_skeleton.SKELETON.values(): skeleton_nodes += nodes
    return set(skeleton_nodes)

class SkeletonPlotter(matsim.network.NetworkPlotter):
    def __init__(self, network, skeleton):
        matsim.network.NetworkPlotter.__init__(self, network)
        self.skeleton = skeleton

    def get_node_style(self, node):
        if node.id in skeleton_nodes:
            return { 'marker' : 'o', 'color' : 'k' }
        return None

class PTLinePlotter(matsim.network.NetworkPlotter):
    def __init__(self, network, route, color):
        matsim.network.NetworkPlotter.__init__(self, network)
        self.route = route
        self.color = color

    def get_link_style(self, link):
        if link.id in self.route:
            return { 'color' : self.color }
        else:
            return None

class StopFacilityPlotter:
    def __init__(self, schedule, route, color):
        self.route = route
        self.schedule = schedule
        self.color = color

    def plot(self):
        for stop in self.route.stops:
            facility = self.schedule.stop_facilities[stop.stop_id]
            plt.plot(facility.coords[0], facility.coords[1], marker = 'o', color = self.color)

network = matsim.network.Network()
matsim.network.NetworkReader(network).read('network_final.xml')

schedule = matsim.transit.TransitSchedule()
matsim.transit.TransitScheduleReader(schedule).read('schedule.xml')

skeleton_nodes = get_skeleton_nodes()

colors = ['r', 'g', 'b', 'c', 'm']
plotters = []

plotters.append(SkeletonPlotter(network, skeleton_nodes))

for line in schedule.lines.values():
    for route in line.routes.values():
        color = colors[int(route.id[4]) - 1]

        plotters.append(PTLinePlotter(network, route.links, color))
        plotters.append(StopFacilityPlotter(schedule, route, color))

plt.figure(figsize=(12, 12))

for plotter in plotters: plotter.plot()

plt.axis('off')
plt.savefig('pt_network.pdf')
