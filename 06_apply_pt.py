import matsim.network
import matsim.transit
import matsim.utils
import matsim.vehicles
import pickle
import numpy as np
import numpy.linalg as la

FIRST_DEPARTURE = '05:00:00'
LAST_DEPARTURE = '23:00:00'
INTERVAL = '01:00:00'

"""
   Generates stops from the approximate positions and line assignments, breaks
   the network links where it is necssary for adding distinct bus stops and
   writes the network and schedules.
"""

with open('routes.dat', 'rb') as f:
    routes = pickle.load(f)

with open('stop_locations.dat', 'rb') as f:
    stop_locations = pickle.load(f)

with open('stop_assignments.dat', 'rb') as f:
    stop_assignments = pickle.load(f)

network = matsim.network.Network()
matsim.network.NetworkReader(network).read('network_clean.xml')

# Step 1: Generate stops per link and align them

stop_locations = np.array(stop_locations)
create_stop_id = lambda index, link: link.id + '_' + str(index)

stops = {}
lines = { line_id : set() for line_id in routes }

class Stop:
    def __init__(self, id, coords, link):
        self.id = id
        self.coords = coords
        self.link = link

for line_id, route in routes.items():
    line_network = network.filter_links(route[1])
    indices = stop_assignments[line_id]

    for index in indices:
        link = line_network.find_closest_link(stop_locations[index])
        stop_id = create_stop_id(index, link)

        if stop_id not in stops:
            coords = line_network.compute_closest_coords_on_link(stop_locations[index], link)
            stops[stop_id] = Stop(stop_id, coords, link)

        lines[line_id].add(stop_id)

# Step 2: Find breakpoints for links that are selected multiple times

breakpoints = {}
links = {}

for stop_id, stop in stops.items():
    if not stop.link.id in links: links[stop.link.id] = []
    links[stop.link.id].append(stop_id)

need_breaks = [link_id for link_id, stop_ids in links.items() if len(stop_ids) > 1]

print('Found %s links that need to be broken up' % len(need_breaks))

for link_id in need_breaks:
    link_stops = [stops[stop_id] for stop_id in links[link_id]]
    link = network.links[link_id]

    start, end = network.get_link_coords(link)
    direction = end - start
    length = la.norm(direction)

    fractions = np.array([la.norm(stop.coords - start) for stop in link_stops]) / length
    differences = np.array([fractions[i] - fractions[i-1] for i in range(1, fractions.shape[0])])
    break_fractions = fractions[:-1] + 0.5 * (fractions[1:] - fractions[:-1])
    breakpoints[link_id] = [start + direction * f for f in break_fractions]

# Step3: Break up links

link_replacements = {}

for link_id, link_breakpoints in breakpoints.items():
    link = network.links[link_id]
    start, end = network.get_link_coords(link)

    break_nodes = []
    for i in range(len(link_breakpoints)):
        break_node_id = link_id + 'b' + str(i)
        break_nodes.append(matsim.network.Node(break_node_id, link_breakpoints[i]))

    involved_nodes = [network.nodes[link.from_node_id]] + break_nodes + [network.nodes[link.to_node_id]]

    break_links = []
    for i in range(1, len(involved_nodes)):
        break_link_id = link_id + 'b' + str(i)
        from_node_id = involved_nodes[i-1].id
        to_node_id = involved_nodes[i].id
        length = la.norm(involved_nodes[i-1].coords - involved_nodes[i].coords)
        attributes = link.attributes

        break_links.append(matsim.network.Link(break_link_id, from_node_id, to_node_id, length, attributes))

    del network.links[link.id]

    for break_node in break_nodes:
        network.nodes[break_node.id] = break_node

    for break_link in break_links:
        network.links[break_link.id] = break_link

    for stop_id in links[link.id]: # Update stops
        stop = stops[stop_id]
        distances = [network.compute_distance_to_link(stop.coords, break_link) for break_link in break_links]
        stop.link = break_links[np.argmin(distances)]

    link_replacements[link_id] = [break_link.id for break_link in break_links]

# Step 4: Save network changes

network.name = 'new_sioux'
matsim.network.NetworkWriter(network).write('network_final.xml')

# Step 5: Create schedules
schedule = matsim.transit.TransitSchedule()
vehicles = matsim.vehicles.VehicleDefinitions()

first_departure = matsim.utils.dtime(FIRST_DEPARTURE)
last_departure = matsim.utils.dtime(LAST_DEPARTURE)
interval = matsim.utils.dtime(INTERVAL)

for stop_id, stop in stops.items():
    stop_facility = matsim.transit.TransitStopFacility(stop_id, stop.coords, stop.link.id, stop_id)
    schedule.stop_facilities[stop_facility.id] = stop_facility

for line_id, route in routes.items():
    route_links = route[1]

    transit_line = matsim.transit.TransitLine(line_id)
    schedule.lines[transit_line.id] = transit_line

    transit_route = matsim.transit.TransitRoute(line_id)
    transit_line.routes[transit_route.id] = transit_route

    # Replace broken up links
    for original_id, replacement in link_replacements.items():
        if original_id in route_links:
            index = route_links.index(original_id)
            route_links[index:index] = replacement

    # Sort the stops along the route
    route_stops = [stops[stop_id] for stop_id in lines[line_id]] # Unordered
    route_indices = [route_links.index(stop.link.id) for stop in route_stops]
    route_indices = np.argsort(route_indices)
    route_stops = [route_stops[index] for index in route_indices]

    # Insert stops and links into the route
    offset = 60

    for stop in route_stops:
        transit_route_stop = matsim.transit.TransitRouteStop(stop.id, matsim.utils.stime(offset))
        transit_route.stops.append(transit_route_stop)
        offset += 60

    for link_id in route_links:
        transit_route.links.append(link_id)

    # Generate departures and busses
    vehicle_count = 0
    departure_time = first_departure

    while departure_time <= last_departure:
        vehicle_id = 'bus_%s_%d' % (line_id, vehicle_count)

        departure = matsim.transit.TransitRouteDeparture(
            vehicle_count, matsim.utils.stime(departure_time), vehicle_id)

        transit_route.departures.append(departure)
        vehicles.vehicles.append(vehicle_id)

        vehicle_count += 1
        departure_time += interval

matsim.vehicles.VehiclesWriter(vehicles).write('vehicles.xml')
matsim.transit.ScheduleWriter(schedule).write('schedule.xml')

# Step 6: Debug info

breakpoint_locations = []
for _breakpoints in breakpoints.values(): breakpoint_locations.extend(_breakpoints)

with open('breakpoints.dat', 'wb+') as f:
    pickle.dump(breakpoint_locations, f)
