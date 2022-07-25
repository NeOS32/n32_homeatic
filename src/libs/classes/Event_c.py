from enum import Enum, auto


class Inputs(Enum):
    SWITCH = auto()
    PIR = auto()
    BLUE = auto()
    TIME_HOUR = auto()
    TIME_MINUTE = auto()
    TIME_SECOND = auto()
    TIME_DAY_OF_WEEK = auto()
    TIME_YEAR = auto()
    TIME_MONTH = auto()
    TIME_DAY = auto()
    TIME_INTERVAL = auto()
    GARAGE_GATE = auto()
    TEMP_HEATING = auto()
    TEMP_WATER = auto()
    TEMP_OUTSIDE = auto()
    TEMP_SYSTEM = auto()
    UNKNOWN = auto()


class Outputs(Enum):
    LIGHT_LED = auto()
    LIGHT_BULB = auto()
    SOCKET = auto()
    PUMP_CIRC = auto()
    HEATER = auto()


class Event_c:
    def __init__(self, name, inputs, outputs, location=None,  debug=False, default_value=0):
        '''default constructor

        Args:
            WiP

        Raises:
            RuntimeError: none at the moment

        Returns:
            nothing since it's a constructor
        '''
        self.inputs = inputs
        self.outputs = outputs
        self._hTable = {
            "name": name,
            "location": location,
            "value": default_value,
            "debug": debug}

    def get_name(self):
        return self._hTable['name']

    def get_value(self):
        return self._hTable['value']

    def get_gramma(self):
        return self._hTable['gramma']

    def get_debug(self):
        return self._hTable['debug']

    def get_location(self):
        return self._hTable['location']

    def set_value(self, value):
        self._hTable['value'] = value

    def add_to_value(self, delta):
        self._hTable['value'] += delta
        return self._hTable['value']

class EventsSnapshot_c:
    def __init__(self, name, inputs, outputs, location=None,  debug=False, default_value=0):
        self.inputs = inputs
        self.outputs = outputs
        self._hTable = {
            "name": name,
            "location": location,
            "value": default_value,
            "debug": debug}
