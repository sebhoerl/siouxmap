from . import utils
import xml.sax
import numpy as np
import matplotlib.pyplot as plt
import re
import numpy.linalg as la

class Network:
    def __init__(self):
        self.path = None
        self.name = None
        self.attributes = {}

        self.links = {}
        self.nodes = {}

    def get_connecting_link(self, from_node_id, to_node_id):
        for link in self.links.values():
            if link.from_node_id == from_node_id and link.to_node_id == to_node_id:
                return link

        return None

    def get_link_coords(self, link):
        start = self.nodes[link.from_node_id].coords
        end = self.nodes[link.to_node_id].coords
        return start, end

    def make_adjacency_list(self):
        adjacency = {}

        for link in self.links.values():
            if link.from_node_id not in adjacency:
                adjacency[link.from_node_id] = set()

            adjacency[link.from_node_id].add(link.to_node_id)

        return adjacency

    def compute_closest_coords_on_link(self, coords, link):
        if coords.shape == (1, 2): coords = np.array(coords).flatten()
        start, end = self.get_link_coords(link)
        difference = end - start
        projection_length = np.dot(difference, coords - start) / la.norm(difference)**2

        if projection_length < 0:
            return start
        elif projection_length > 1:
            return end
        else:
            return start + difference * projection_length

    def find_closest_link(self, coords):
        minimum_distance = np.inf
        minimum_id = None

        for link_id in sorted(self.links):
            location = self.compute_closest_coords_on_link(coords, self.links[link_id])
            distance = la.norm(location - coords)

            if distance < minimum_distance:
                minimum_distance = distance
                minimum_id = link_id

        return self.links[minimum_id]

    def compute_distance_to_link(self, coords, link):
        closest = self.compute_closest_coords_on_link(coords, link)
        return la.norm(coords - closest)

    def filter_links(self, links):
        network = Network()
        network.name = self.name
        network.attributes = self.attributes

        for link_id in links:
            link = self.links[link_id]
            network.links[link.id] = link
            network.nodes[link.from_node_id] = self.nodes[link.from_node_id]
            network.nodes[link.to_node_id] = self.nodes[link.to_node_id]

        return network

    def filter(self, filter):
        filtered_nodes = {}
        filtered_links = {}

        for node_id, node in self.nodes.items():
            if filter(node): filtered_nodes[node_id] = node

        for link_id, link in self.links.items():
            if link.from_node_id in filtered_nodes and link.to_node_id in filtered_nodes:
                filtered_links[link_id] = link

        network = Network()
        network.nodes = filtered_nodes
        network.links = filtered_links
        network.name = self.name
        network.attributes = self.attributes

        return network

class Node:
    def __init__(self, id, coords):
        self.id = id
        self.coords = coords

class Link:
    def __init__(self, id, from_node_id, to_node_id, length, attributes):
        self.id = id
        self.from_node_id = from_node_id
        self.to_node_id = to_node_id
        self.length = float(length)
        self.attributes = attributes

class NetworkReader(xml.sax.ContentHandler):
    def __init__(self, network):
        self.network = network
        self.links = {}
        self.nodes = {}

    def read(self, path):
        self.network.path = path

        self.links = {}
        self.nodes = {}

        with utils.open_by_extension(path) as f:
            xml.sax.parse(f, self)

        self.network.links = self.links
        self.network.nodes = self.nodes

    def _read_coords(self, attributes):
        return np.array((attributes['x'], attributes['y'])).astype(np.float)

    def _read_node(self, attributes):
        id = attributes['id']
        self.nodes[id] = Node(id, self._read_coords(attributes))

    def _read_link(self, attributes):
        id = attributes['id']
        from_node_id = attributes['from']
        to_node_id = attributes['to']
        length = attributes['length']
        attribs = {}

        for key, value in attributes.items():
            if key in ('id', 'from', 'to', 'length'): continue
            attribs[key] = value

        self.links[id] = Link(id, from_node_id, to_node_id, length, attribs)

    def startElement(self, name, attributes):
        if name == 'node':
            self._read_node(attributes)

        if name == 'link':
            self._read_link(attributes)

        if name == 'links':
            self.network.attributes = attributes

        if name == 'network':
            if 'name' in attributes:
                self.network.name = attributes['name']

class NetworkPlotter:
    def __init__(self, network):
        self.network = network
        self.ax = None

    def plot(self, ax = None):
        self.ax = ax if ax is not None else plt.gca()

        for node_id, node in self.network.nodes.items():
            self.plot_node(node)

        for link_id, link in self.network.links.items():
            start = self.network.nodes[link.from_node_id].coords
            end = self.network.nodes[link.to_node_id].coords
            self.plot_link(link, start, end)

    def get_link_style(self, link):
        return { 'color' : 'k', 'linestyle' : '-' }

    def get_node_style(self, node):
        return None

    def plot_link(self, link, start, end, style = None):
        style = self.get_link_style(link) if style is None else style

        if style is not None:
            self.ax.plot([start[0], end[0]], [start[1], end[1]], **style)

    def plot_node(self, node):
        style = self.get_node_style(node)

        if style is not None:
            self.ax.plot(node.coords[0], node.coords[1], **style)

class NetworkTransformer:
    def transform(self, source, target):
        with utils.open_by_extension(target, 'w+') as output_file:
            with utils.open_by_extension(source) as input_file:
                for line in input_file:
                    if '<node ' in line:
                        node_id = re.search(' id="(.+?)"', line).group(1)
                        line = self.transform_node(node_id, line)

                    elif '<link ' in line:
                        link_id = re.search(' id="(.+?)"', line).group(1)
                        line = self.transform_link(link_id, line)

                    elif '</links>' in line:
                        line = self.insert_links() + line

                    elif '</nodes>' in line:
                        line = self.insert_nodes() + line

                    if not line is None:
                        output_file.write(line)

    def transform_link(self, id, line):
        return line

    def transform_node(self, id, line):
        return line

    def insert_links(self):
        return ''

    def insert_nodes(self):
        return ''

class DijkstraCache:
    def __init__(self, network):
        self.adjacency_list = network.make_adjacency_list()
        self.network = network

        self.outgoing = { node_id : set() for node_id in network.nodes.keys() }
        self.incoming = { node_id : set() for node_id in network.nodes.keys() }

        for link in network.links.values():
            self.outgoing[link.from_node_id].add(link.id)
            self.incoming[link.to_node_id].add(link.id)

    def get_connecting_link_id(self, from_node_id, to_node_id):
        outgoing = self.outgoing[from_node_id]
        incoming = self.incoming[to_node_id]
        hits = set(outgoing).intersection(set(incoming))

        if len(hits) == 1:
            return hits.pop()
        elif len(hits) == 0:
            return None
        else:
            raise RuntimeError('Network contains duplicate links: ' + repr(hits))

class Dijkstra:
    def __init__(self, network, cache = None):
        self.cache = cache if cache is not None else DijkstraCache(network)
        self.network = network

    def compute_cost(self, link):
        return 1

    def find_route(self, from_node_id, to_node_id):
        # Prepare data structures
        node_map = list(self.network.nodes.keys())

        distances = np.array([np.inf] * len(node_map))
        previous = [None] * len(node_map)

        pending = list(range(len(node_map)))

        distances[node_map.index(from_node_id)] = 0
        target = node_map.index(to_node_id)

        # Traverse the network
        while len(pending) > 0:
            current = pending[np.argmin(distances[pending])]
            pending.remove(current)

            if current == target: break

            for destination in self.cache.adjacency_list[node_map[current]]:
                destination = node_map.index(destination)

                link_id = self.cache.get_connecting_link_id(node_map[current], node_map[destination])
                proposal = distances[current] + self.compute_cost(self.network.links[link_id])

                if proposal < distances[destination]:
                    distances[destination] = proposal
                    previous[destination] = current

        # Build route in indices
        route = []
        current = target

        while previous[current] is not None:
            route.append(current)
            current = previous[current]

        route.append(current)
        route = list(reversed(route))

        # Get node IDs
        nodes = [node_map[index] for index in route]

        # Get links IDs
        links = [self.cache.get_connecting_link_id(nodes[i-1], nodes[i]) for i in range(1, len(nodes))]

        return nodes, links, distances[target]

class NetworkWriter:
    def __init__(self, network):
        self.network = network

    def _write_nodes(self, f):
        f.write('    <nodes>\n')

        for node in self.network.nodes.values():
            f.write('        ' + '<node id="%s" x="%f" y="%f" />\n' % (node.id, node.coords[0], node.coords[1]))

        f.write('    </nodes>\n')

    def _render_attributes(self, attributes):
        values = attributes.values()
        keys = attributes.keys()
        return ' '.join(['%s="%s"' % (key, value) for key, value in zip(keys, values)])

    def _write_links(self, f):
        f.write('    <links %s>\n' % self._render_attributes(self.network.attributes))

        for link in self.network.links.values():
            args = (link.id, link.from_node_id, link.to_node_id, link.length, self._render_attributes(link.attributes))
            f.write('        ' + '<link id="%s" from="%s" to="%s" length="%f" %s />\n' % args)

        f.write('    </links>\n')

    def write(self, path):
        with utils.open_by_extension(path, 'w+') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v1.dtd">\n')
            f.write('<network name="%s">\n' % self.network.name)

            self._write_nodes(f)
            self._write_links(f)

            f.write('</network>')
