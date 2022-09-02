import libs.classes.Synchro_c as Synchro_m


class Reg4Commands_c:  # singletone
    __instance = None
    _lock = Synchro_m.Synchro_c()
    _persist_methods = ['get', 'save', 'delete', 'asdf']

    @staticmethod
    def getInstance():
        with self._lock:
            """ Static access method. """
            if None == Reg4Commands_c.__instance:
                Reg4Commands_c()

        return Reg4Commands_c.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if None != self.__instance:
            raise Exception("This class is a singleton!")
        else:
            self.__instance = self
            self._hTable = {}
            self._hTracking = {}

    def add_action(self, location, cmnd, value=''):
        with self._lock:
            if not location in self._hTable:
                self._hTable[location] = {}
            if value in self._hTable[location]:
                raise Exception(
                    f"Value: '{value}' already defined for location: '{location}'!")
            self._hTable[location][value] = cmnd

    def get_value(self, location, action):
        with self._lock:
            if location in self._hTable:
                if action in self._hTable[location]:
                    return self._hTable[location][action]
            raise Exception(
                f"Location='{location}' or action='{action}' not yet registered!")

    def assign(self, name, value):
        with self._lock:
            self._hTable[name].set_value(value)
