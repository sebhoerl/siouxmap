from matsim.utils import open_by_extension
import matsim.network
import pyproj
import re

"""
    Transforms the network from network_josm.xml (from JOSM)
    to a one in network_transformed.xml, which is compatible with
    the coordinate system that is used in the original Sioux Falls
    scenario.
"""

source_projection = pyproj.Proj(init='EPSG:3857') # Output by JOSM
target_projection = pyproj.Proj(init='EPSG:26914') # Format of original Sioux-2014

xregex = re.compile('x="([-eE0-9\.]+)"')
yregex = re.compile('y="([0-9\.]+)"')

class Transformer(matsim.network.NetworkTransformer):
    def get_coords(self, line):
        matchx = re.search(xregex, line)
        matchy = re.search(yregex, line)
        return matchx.group(1), matchy.group(1)

    def transform_node(self, node_id, line):
        x, y = self.get_coords(line)
        x, y = pyproj.transform(source_projection, target_projection, x, y)

        line = re.sub(xregex, 'x="%f"' % x, line)
        line = re.sub(yregex, 'y="%f"' % y, line)

        return line

Transformer().transform('network_josm.xml', 'network_transformed.xml')
