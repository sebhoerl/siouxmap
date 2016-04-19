import matsim.network
import matsim.transit
import pickle
import numpy as np
import numpy.linalg as la
import matplotlib.pyplot as plt

"""
   Starts a tool to first choose approximate stop locations and then which stops
   should belong to which lines. Later on the stops will be refined and put on
   the right lanes for the respective pt lines.
"""

class PTLinePlotter(matsim.network.NetworkPlotter):
    def __init__(self, network, route):
        matsim.network.NetworkPlotter.__init__(self, network)
        self.route = route

    def get_link_style(self, link):
        if link.id in self.route:
            return { 'color' : 'b' }
        else:
            return None

network = matsim.network.Network()
matsim.network.NetworkReader(network).read('network_clean.xml')

schedule = matsim.transit.TransitSchedule()
matsim.transit.TransitScheduleReader(schedule).read('siouxfalls-2014/Siouxfalls_transitSchedule.xml')

with open('routes.dat', 'rb') as f:
    routes = pickle.load(f)

locations = []

## Step 1: Capture all stop locations

def select_stop_location(event):
    print(event.xdata, event.ydata)
    locations.append(np.array((event.xdata, event.ydata)))

    plt.plot(event.xdata, event.ydata, 'or')
    plt.draw()

figure = plt.figure()
figure.canvas.mpl_connect('button_press_event', select_stop_location)

network_plotter = matsim.network.NetworkPlotter(network)
network_plotter.plot()

for line_id in schedule.lines:
    for facility in schedule.get_line_facilities(line_id):
        plt.plot(facility.coords[0], facility.coords[1], 'or', alpha = 0.25)

for line, route in routes.items():
    plotter = PTLinePlotter(network, route[1])
    plotter.plot()

plt.show()

with open('stop_locations.dat', 'wb+') as f:
    pickle.dump(locations, f)


## Step 2: Select which stops belong to which lines

current_line = None
line_assignments = { line_id : [] for line_id in routes }

def assign_stop_location(event):
    location = np.array((event.xdata, event.ydata))
    index = np.argmin(la.norm(locations - location, axis = 1))
    line_assignments[current_line].append(index)

    plt.plot(locations[index][0], locations[index][1], 'ob')
    plt.draw()

for line_id, route in routes.items():
    current_line = line_id

    figure = plt.figure()
    plt.title(line_id)

    figure.canvas.mpl_connect('button_press_event', assign_stop_location)

    network_plotter.plot()

    plotter = PTLinePlotter(network, route[1])
    plotter.plot()

    for location in locations:
        plt.plot(location[0], location[1], 'or')

    plt.show()

with open('stop_assignments.dat', 'wb+') as f:
    pickle.dump(line_assignments, f)
