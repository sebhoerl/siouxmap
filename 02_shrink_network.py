from matsim.utils import open_by_extension
import matsim.network
import matsim.facilities
import numpy.linalg as la
import numpy as np
import re, pickle

THRESHOLD = 500

"""
    Shrinks the network in a way that a bounding box around all the facility
    locations from the original facilities file is generated with an additional
    configurable threshold. Crossing links are shortened while outside nodes and
    links are deleted.

    Input is network_transformed.xml and output is network_shrunk.xml.
"""

# Load network and facilities

network = matsim.network.Network()
matsim.network.NetworkReader(network).read('network_transformed.xml')

facility_ids, facility_coords = [], []

for id, facility in matsim.facilities.FacilitiesReader().read('siouxfalls-2014/Siouxfalls_facilities.xml.gz').items():
    facility_ids.append(id)
    facility_coords.append(facility.coords)

facility_coords = np.array(facility_coords)

# Find bounding box

minimum = np.min(facility_coords, axis=0)
maximum = np.max(facility_coords, axis=0)

minimum -= THRESHOLD
maximum += THRESHOLD

# Find all outside nodes

is_outside = lambda x: (x < minimum).any() or (x > maximum).any()
outside_nodes = [node_id for node_id, node in network.nodes.items() if is_outside(node.coords)]

# Find all links that are completely outside or crossing the boundary

outside_links = []
crossing_links = []

for link_id, link in network.links.items():
    from_outside = link.from_node_id in outside_nodes
    to_outside = link.to_node_id in outside_nodes

    if from_outside and to_outside:
        outside_links.append(link)
    elif from_outside or to_outside:
        crossing_links.append(link)
        #outside_links.append(link)

# Move the outside node of the crossing links

moved_nodes = []

for link in crossing_links:
    node_id = link.from_node_id if link.from_node_id in outside_nodes else link.to_node_id
    node = network.nodes[node_id]
    moved_nodes.append(node_id)

    # TODO: Could be improved by finding the actual intersection point
    node.coords[0] = max(node.coords[0], minimum[0])
    node.coords[0] = min(node.coords[0], maximum[0])
    node.coords[1] = max(node.coords[1], minimum[1])
    node.coords[1] = min(node.coords[1], maximum[1])

# Find the nodes that haven't been moved (and thus can be deleted)

outside_nodes = set(outside_nodes).difference(set(moved_nodes))

# Remove nodes and links
for node_id in outside_nodes: del network.nodes[node_id]
for link in outside_links: del network.links[link.id]

# Write changes
class Transformer(matsim.network.NetworkTransformer):
    def transform_node(self, node_id, line):
        if node_id in network.nodes:
            node = network.nodes[node_id]

            line = re.sub(' x="(.+?)"', ' x="%f"' % node.coords[0], line)
            line = re.sub(' y="(.+?)"', ' y="%f"' % node.coords[1], line)

            return line
        else:
            return None

    def transform_link(self, id, line):
        return None if not id in network.links else line

Transformer().transform('network_transformed.xml', 'network_shrunk.xml')

print('Found %d crossing links and %d outside' % (len(crossing_links), len(outside_links)))

# Write debug information
with open('network_shrunk.dat', 'wb+') as f:
    outside_links = [link.id for link in outside_links]
    crossing_links = [link.id for link in crossing_links]
    pickle.dump((outside_links, crossing_links, outside_nodes, moved_nodes), f)
