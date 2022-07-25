class Reg4vars_c:  # singletone
    """
    It's a registry maintaining variables with values.
    """
    __instance = None
    _persist_methods = ['get', 'save', 'delete', 'asdf']

    def __init__(self):
        """ Virtual private constructor. """
        if self.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            self.__instance = self
            self._hTable = {}
            self._hTracking = {}

    @staticmethod
    def getInstance():
        """ Static access method. """
        if self.__instance == None:
            Reg4vars_c()
        return Reg4vars_c.__instance

    def add(self, var):
        self._hTable[var.get_name()] = var
        if None != var.get_location():
            self._hTracking[var.get_location()] = var

    def get_value(self, name):
        return self._hTable[name].get_value()

    def get_var(self, name):
        if name in self._hTable:
            return self._hTable[name]
        else:
            raise Exception(f"ERR: '{name}' variable not yet registered")

    def assign(self, name, value):
        self._hTable[name].set_value(value)

    def is_stored(self, name):
        if name in self._hTable:
            return True
        else:
            return False

    def is_tracked(self, location):
        if location in self._hTracking:
            return True
        else:
            return False

    def get_tracked_var(self, location):
        if location in self._hTracking:
            return self._hTracking[location]
        else:
            raise NameError(
                f"ERR: Tracked location '{location}' hasn't been stored")
