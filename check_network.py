import matsim.network

network = matsim.network.Network()
matsim.network.NetworkReader(network).read('network_final.xml')
#matsim.network.NetworkReader(network).read('siouxfalls-2014/Siouxfalls_network_PT.xml')

# Check links
pairs = {}
count = 0

for link in network.links.values():
    if not link.from_node_id in network.nodes or not link.to_node_id in network.nodes:
        count += 1

    pair = (link.from_node_id, link.to_node_id)
    if not pair in pairs: pairs[pair] = []
    pairs[pair].append(link)

print('Found %d links with non-existant nodes' % count)

count = 0

for pair, links in pairs.items():
    if len(links) > 1:
        count += 1

print('Found %d duplicate links' % count)

# Check nodes
outgoing = { id : 0 for id in network.nodes.keys() }
incoming = { id : 0 for id in network.nodes.keys() }

for link in network.links.values():
    outgoing[link.from_node_id] += 1
    incoming[link.to_node_id] += 1

sources = set()
sinks = set()

for node_id, count in outgoing.items():
    if count == 0: sinks.add(node_id)

for node_id, count in incoming.items():
    if count == 0: sources.add(node_id)

detached = sources.intersection(sinks)
sources = sources.difference(detached)
sinks = sinks.difference(detached)

print('Found %d detached nodes' % len(detached))
print('Found %d sinks' % len(sinks))
print('Found %d sources' % len(sources))

count = 0

for node_id in network.nodes.keys():
    connected = 0

    for link in network.links.values():
        if node_id == link.from_node_id: connected += 1
        if node_id == link.to_node_id: connected += 1

    if connected == 0:
        count += 1

print('Found %d orphaned nodes' % count)
