from matsim.utils import open_by_extension
import matsim.network
import numpy.linalg as la
import os, pickle, re

SEED_NODE_ID = '80693033'

"""
    Reads network_shrunk.xml and
        1. updates all the lengths (due to transformation and shrinkage)
        2. searches for soures and sinks and deletes them
        3. searches for and removes detached cyckles from the main network
        4. search for and removes duplicate links (same from/to nodes)

    In order to define which subset is the main network, SEED_NODE_ID must
    be defined to a node, which is in the main network.

    Output is to network_clean.xml
"""

network = matsim.network.Network()
matsim.network.NetworkReader(network).read('network_shrunk.xml')

removed_nodes = []
removed_links = []

# Step 1: Update correct link lengths

for link in network.links.values():
    start, end = network.get_link_coords(link)
    link.length = la.norm(end - start)

# Step 2: Search for sink and sources

iteration = 0

while True:
    outgoing = { id : 0 for id in network.nodes.keys() }
    incoming = { id : 0 for id in network.nodes.keys() }

    for link in network.links.values():
        outgoing[link.from_node_id] += 1
        incoming[link.to_node_id] += 1

    iteration_sinks = [id for id, count in outgoing.items() if count == 0]
    iteration_sources = [id for id, count in incoming.items() if count == 0]

    iteration += 1
    print('Iteration %d: Found %d sinks and %d sources' % (iteration, len(iteration_sinks), len(iteration_sources)))

    # Remove those nodes from the network
    for node_id in iteration_sinks:
        removed_nodes.append(node_id)
        del network.nodes[node_id]

    for node_id in iteration_sources:
        removed_nodes.append(node_id)
        del network.nodes[node_id]

    # Remove loose links from the network
    for link_id in list(network.links.keys()):
        from_id = network.links[link_id].from_node_id
        to_id = network.links[link_id].to_node_id

        if from_id not in network.nodes or to_id not in network.nodes:
            removed_links.append(link_id)
            del network.links[link_id]

    if len(iteration_sinks) == 0 and len(iteration_sources) == 0: break

print('Removed %d links' % len(removed_links))

# Step 3: Search for unreachable regions / orphaned nodes

adjacency_list = network.make_adjacency_list()

pending = set()
visited = set()
pending.add(SEED_NODE_ID)

# Traverse network
while len(pending) > 0:
    current = pending.pop()
    visited.add(current)

    for destination in adjacency_list[current]:
        if not destination in visited:
            pending.add(destination)

# Find the ones that have not been visited
detached_nodes = set(list(network.nodes.keys())).difference(visited)

# Find the corresponding links
is_detached = lambda x: x.from_node_id in detached_nodes or x.to_node_id in detached_nodes
detached_links = [link.id for link in network.links.values() if is_detached(link)]

for node_id in detached_nodes: del network.nodes[node_id]
for link_id in detached_links: del network.links[link_id]

print('Found %d detached nodes and %d links' % (len(detached_nodes), len(detached_links)))

# Step 4: Find duplicate links

combined_ids = {}

for link in network.links.values():
    combined_id = (link.from_node_id, link.to_node_id)

    if combined_id not in combined_ids:
        combined_ids[combined_id] = []

    combined_ids[combined_id].append(link)

duplicates = []

for combined_id, links in combined_ids.items():
    if len(links) > 0: duplicates += links[1:]

for duplicate in duplicates:
    del network.links[duplicate.id]

print('Found %d duplicate links' % len(duplicates))

# Step 5: Write changes

class Transformer(matsim.network.NetworkTransformer):
    def transform_link(self, id, line):
        if not id in network.links: return None
        return re.sub('length="(.+?)"', 'length="%f"' % network.links[id].length, line)

    def transform_node(self, id, line):
        return None if not id in network.nodes else line

Transformer().transform('network_shrunk.xml', 'network_clean.xml')

# Step 6: Debug information

with open('adjacency_list.dat', 'wb+') as f:
    pickle.dump(adjacency_list, f)

with open('network_clean.dat', 'wb+') as f:
    pickle.dump((removed_nodes, removed_links, detached_nodes, detached_links, duplicates), f)
