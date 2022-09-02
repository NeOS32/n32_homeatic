import libs.classes.Reg4Configs_c as Reg4Configs_m
import libs.classes.Synchro_c as Synchro_m
import libs.classes.var_c as var_m
from collections import defaultdict


class Reg4vars_c:  # singletone
    """
    It's a registry maintaining variables with values.
    """
    __instance = None
    _persist_methods = ['get', 'save', 'delete', 'asdf']

    # See PEP-0343 for context managers discussion
    _lock = Synchro_m.Synchro_c()

    def __init__(self):
        """ Virtual private constructor. """
        if self.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            self.__instance = self
            self._hTable = {}  # name => var (1:1)
            self._hLocation = defaultdict(dict)  # location => var (1:n)

    @staticmethod
    def getInstance():
        """ Static access method. """
        with Reg4vars_c._lock:
            if None == Reg4vars_c.__instance:
                Reg4vars_c()

        return Reg4vars_c.__instance

    def addVar(self, var):
        with self._lock:
            self._hTable[var.get_name()] = var
            loc = var.get_location()
            if None != loc:
                self._hLocation[var.get_location()][var.get_name()] = var

    def get_value(self, name):
        with self._lock:
            return self.get_var(name).get_value()

    def get_var(self, name):
        with self._lock:
            return self._hTable.get(name)

    def assign(self, name, value):
        with self._lock:
            self._hTable.get(name).set_value(value)

    def is_stored(self, name):
        with self._lock:
            return name in self._hTable

    def is_tracked(self, location):
        with self._lock:
            return location in self._hLocation

    def get_tracked_var_yield(self, location):
        with self._lock:
            h = self._hLocation.get(location)
            if h:
                for v in self._hLocation.get(location).keys():
                    yield h.get(v)

    def addConfig(self, extra_namespace, file_name=None, env_var_with_filename=None):
        Reg4Configs_m.Reg4Configs_c.getInstance().addConfig(
            extra_namespace=extra_namespace, file_name=file_name, env_var_with_filename=env_var_with_filename)

    def InstantiateVars(self, extra_namespace):
        for k, h in Reg4Configs_m.Reg4Configs_c.getInstance().getConfigYield([extra_namespace]):
            # a variable instantiation
            var = var_m.var_c(name=k,
                              event_class="???",
                              location=h.get('path'),
                              gramma=h.get('gramma', "MajorQuant"),
                              debug=h.get('debug'),
                              regex=h.get('regex'),
                              default_value=h.get('default_value')
                              )

            self.addVar(var)
