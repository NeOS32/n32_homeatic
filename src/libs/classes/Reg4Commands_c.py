class Reg4Commands_c:  # singletone
    __instance = None
    _persist_methods = ['get', 'save', 'delete', 'asdf']

    def __init__(self):
        """ Virtually private constructor. """
        if None != self.__instance:
            raise Exception("This class is a singleton!")
        else:
            self.__instance = self
            self._hTable = {}
            self._hTracking = {}

    @staticmethod
    def getInstance():
        """ Static access method. """
        if self.__instance == None:
            Reg4Commands_c()
        return self.__instance

    def add_action(self, location, cmnd, value='' ):
        if not location in self._hTable:
            self._hTable[location] = {}
        if value in self._hTable[location]:
            raise Exception(
                f"Value: '{value}' already defined for location: '{location}'!")
        self._hTable[location][value] = cmnd

    def get_value(self, location, action):
        if location in self._hTable:
            if action in self._hTable[location]:
                return self._hTable[location][action]
        raise Exception(
            f"Location='{location}' or action='{action}' not yet registered!")

    def assign(self, name, value):
        self._hTable[name].set_value(value)
