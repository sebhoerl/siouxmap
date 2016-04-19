from . import utils
import xml.sax
import numpy as np

class Facility:
    def __init__(self, id, coords):
        self.id = id
        self.coords = coords

class FacilitiesReader(xml.sax.ContentHandler):
    def __init__(self):
        self.reset()

    def reset(self):
        self.facilities = {}

    def read(self, path):
        self.reset()

        with utils.open_by_extension(path) as f:
            xml.sax.parse(f, self)

        return self.facilities

    def startElement(self, name, attributes):
        if name == 'facility':
            self._read_facility(attributes)

    def _read_facility(self, attributes):
        id, x, y = (attributes[k] for k in ('id', 'x', 'y'))
        self.facilities[id] = Facility(id, np.array((x,y)).astype(np.float))
