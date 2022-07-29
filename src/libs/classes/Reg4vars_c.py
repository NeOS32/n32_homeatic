import libs.classes.Reg4Configs_c as Reg4Configs_m
import libs.classes.var_c as var_c
from collections import defaultdict
import threading

# See PEP-0343 for context managers discussion
_semVars = threading.BoundedSemaphore(value=1)


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
            self._hTable = {}  # name => var (1:1)
            self._hLocation = defaultdict(dict)  # location => var (1:n)

    @staticmethod
    def getInstance():
        """ Static access method. """

        _semVars.acquire()
        if None == self.__instance:
            Reg4vars_c()
        _semVars.release()

        return Reg4vars_c.__instance

    def addVar(self, var):

        _semVars.acquire()
        self._hTable[var.get_name()] = var
        loc = var.get_location()
        if None != loc:
            self._hLocation[var.get_location()][var.get_name()] = var
        _semVars.release()

    def get_value(self, name):

        _semVars.acquire()
        value = self.get_var(name).get_value()
        _semVars.release()

        return value

    def get_var(self, name):

        _semVars.acquire()
        var = self._hTable.get(name)
        _semVars.release()

        return var

    def assign(self, name, value):

        _semVars.acquire()
        self._hTable.get(name).set_value(value)
        _semVars.release()

    def is_stored(self, name):

        _semVars.acquire()
        b = name in self._hTable
        _semVars.release()

        return b

    def is_tracked(self, location):

        _semVars.acquire()
        b = location in self._hLocation
        _semVars.release()

        return b

    def get_tracked_var_yield(self, location):

        _semVars.acquire()
        h = self._hLocation.get(location)
        if h:
            for v in self._hLocation.get(location).keys():
                yield h.get(v)
        _semVars.release()

    def addConfig(self, extra_namespace, file_name=None, env_var_with_filename=None):
        Reg4Configs_m.Reg4Configs_c.getInstance().addConfig(
            extra_namespace=extra_namespace, file_name=file_name, env_var_with_filename=env_var_with_filename)

    def InstantiateVars(self, extra_namespace):

        for k, h in Reg4Configs_m.Reg4Configs_c.getInstance().getConfigYield([extra_namespace]):

            # a variable instantiation
            var = var_c.var_c(name=k,
                              event_class="???",
                              location=h.get('path'),
                              gramma=h.get('gramma'),
                              debug=h.get('debug'),
                              regex=h.get('regex'),
                              default_value=h.get('default_value')
                              )

            self.addVar(var)
