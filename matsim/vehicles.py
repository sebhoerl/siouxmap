from . import utils

VEHICLE_TYPE = """
    <vehicleType id="Bus MAN NL323F">
        <capacity>
            <seats persons="38"/>
            <standingRoom persons="52"/>
        </capacity>
        <length meter="7.5"/>
        <width meter="1.0"/>
        <accessTime secondsPerPerson="1.0"/>
        <egressTime secondsPerPerson="1.0"/>
        <doorOperation mode="serial"/>
        <passengerCarEquivalents pce="1.0"/>
    </vehicleType>
"""[1:]

TYPE = 'Bus MAN NL323F'

class VehicleDefinitions:
    def __init__(self):
        self.vehicles = []

class VehiclesWriter:
    def __init__(self, definitions):
        self.definitions = definitions

    def write(self, path):
        with utils.open_by_extension(path, 'w+') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<vehicleDefinitions xmlns="http://www.matsim.org/files/dtd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.matsim.org/files/dtd http://www.matsim.org/files/dtd/vehicleDefinitions_v1.0.xsd">\n')
            f.write(VEHICLE_TYPE)

            for vehicle_id in self.definitions.vehicles:
                f.write('    <vehicle id="%s" type="%s"/>\n' % (vehicle_id, TYPE))

            f.write('</vehicleDefinitions>')
