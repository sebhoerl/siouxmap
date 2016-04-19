from . import utils
import xml.sax
import numpy as np
import matplotlib.pyplot as plt
import re

class TransitSchedule:
    def __init__(self):
        self.stop_facilities = {}
        self.lines = {}

    def get_line_facilities(self, line_id):
        line = self.lines[line_id]
        facilities = set()

        for route in line.routes.values():
            for stop in route.stops:
                facilities.add(self.stop_facilities[stop.stop_id])

        return facilities

class TransitStopFacility:
    def __init__(self, id, coords, link_id, name):
        self.id = id
        self.coords = coords
        self.link_id = link_id
        self.name = name

class TransitLine:
    def __init__(self, id):
        self.id = id
        self.routes = {}

class TransitRoute:
    def __init__(self, id):
        self.id = id

        self.stops = []
        self.links = []
        self.departures = []

class TransitRouteStop:
    def __init__(self, stop_id, offset):
        self.stop_id = stop_id
        self.offset = offset

class TransitRouteDeparture:
    def __init__(self, id, departure_time, vehicle_id):
        self.id = id
        self.departure_time = departure_time
        self.vehicle_id = vehicle_id

class TransitScheduleReader(xml.sax.ContentHandler):
    def __init__(self, schedule):
        self.schedule = schedule
        self.reset()

    def read(self, path):
        self.reset()

        with utils.open_by_extension(path) as f:
            xml.sax.parse(f, self)

    def reset(self):
        self.line = None
        self.route = None

    def _read_transit_route_stop(self, transit_route, attributes):
        transit_route.stops.append(TransitRouteStop(attributes['refId'], attributes['departureOffset']))

    def _read_transit_route_link(self, transit_route, attributes):
        transit_route.links.append(attributes['refId'])

    def _read_transit_route(self, transit_line, attributes):
        route = TransitRoute(attributes['id'])
        transit_line.routes[route.id] = route
        return route

    def _read_transit_line(self, schedule, attributes):
        line = TransitLine(attributes['id'])
        schedule.lines[line.id] = line
        return line

    def _read_transit_stop_facility(self, schedule, attributes):
        id = attributes['id']
        coords = self._read_coords(attributes)
        link_id = attributes['linkRefId']
        name = attributes['name']

        facility = TransitStopFacility(id, coords, link_id, name)
        schedule.stop_facilities[facility.id] = facility

    def _read_coords(self, attributes):
        return np.array((attributes['x'], attributes['y'])).astype(np.float)

    def startElement(self, name, attributes):
        if name == 'stopFacility':
            self._read_transit_stop_facility(self.schedule, attributes)

        if name == 'transitLine':
            self.line = self._read_transit_line(self.schedule, attributes)

        if name == 'transitRoute' and self.line is not None:
            self.route = self._read_transit_route(self.line, attributes)

        if name == 'stop' and self.route is not None:
            self._read_transit_route_stop(self.route, attributes)

        if name == 'link' and self.route is not None:
            self._read_transit_route_link(self.route, attributes)

    def endElement(self, name):
        if name == 'transitLine': self.line = None
        if name == 'transitRoute': self.route = None

class ScheduleWriter:
    def __init__(self, schedule):
        self.schedule = schedule
        self.handle = None
        self.indent = 0

    def _write(self, line):
        self.handle.write(('    ' * self.indent) + line + '\n')

    def _render_attributes(self, attributes):
        return ' '.join(['%s="%s"' % (key, value) for key, value in attributes.items()])

    def _write_facility(self, facility):
        attributes = self._render_attributes({
            'id' : facility.id,
            'x' : facility.coords[0],
            'y' : facility.coords[1],
            'linkRefId' : facility.link_id,
            'name' : facility.name
        })

        self._write('<stopFacility %s />' % attributes)

    def _write_stop_facilities(self):
        self._write('<transitStops>')
        self.indent += 1

        for facility in self.schedule.stop_facilities.values():
            self._write_facility(facility)

        self.indent -= 1
        self._write('</transitStops>')

    def _write_route_stop(self, stop):
        self._write('<stop refId="%s" arrivalOffset="%s" departureOffset="%s" awaitDeparture="false"/>' % (stop.stop_id, stop.offset, stop.offset))

    def _write_route_link(self, link):
        self._write('<link refId="%s"/>' % link)

    def _write_route_departure(self, departure):
        self._write('<departure id="%s" departureTime="%s" vehicleRefId="%s"/>' % (departure.id, departure.departure_time, departure.vehicle_id))

    def _write_route(self, route):
        self._write('<transitRoute id="%s">' % route.id)
        self.indent += 1

        self._write('<transportMode>bus</transportMode>')

        self._write('<routeProfile>')
        self.indent += 1

        for stop in route.stops:
            self._write_route_stop(stop)

        self.indent -= 1
        self._write('</routeProfile>')

        self._write('<route>')
        self.indent += 1

        for link in route.links:
            self._write_route_link(link)

        self.indent -= 1
        self._write('</route>')

        self._write('<departures>')
        self.indent += 1

        for departure in route.departures:
            self._write_route_departure(departure)

        self.indent -= 1
        self._write('</departures>')

        self.indent -= 1
        self._write('</transitRoute>')

    def _write_line(self, line):
        self._write('<transitLine id="%s">' % line.id)
        self.indent += 1

        for route in line.routes.values():
            self._write_route(route)

        self.indent -= 1
        self._write('</transitLine>')

    def _write_lines(self):
        for line in self.schedule.lines.values():
            self._write_line(line)

    def write(self, path):
        self.handle = utils.open_by_extension(path, 'w+')

        self._write('<?xml version="1.0" encoding="UTF-8"?>')
        self._write('<!DOCTYPE transitSchedule SYSTEM "http://www.matsim.org/files/dtd/transitSchedule_v1.dtd">')

        self._write('<transitSchedule>')
        self.indent += 1

        self._write_stop_facilities()
        self._write_lines()

        self.indent -= 1
        self._write('</transitSchedule>')

        self.handle.close()
