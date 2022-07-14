from collections import deque
import json

        
class Reg4Configs_c(object):  # singletone
    __instance = None
    _persist_methods = ['get', 'save', 'delete', 'asdf']

    @staticmethod
    def getInstance():
        """ Static access method. """
        if None == Reg4Configs_c.__instance:
            Reg4Configs_c.__instance = Reg4Configs_c()
        return Reg4Configs_c.__instance
    
    def __init__(self):
        """ Virtually private constructor. """
        
        # singleton stuff
        if None != Reg4Configs_c.__instance:
            raise Exception("This class is a singleton!")
        else:
            Reg4Configs_c.__instance = self

        # other stuff
        # self.logging = logging
        self._hTable= {}


    def addConfig(self, prefix, file_name):
        # reading a JSON
        if not prefix in self._hTable:
            self._hTable[prefix] = {}
        else:
            self.logging.warn(
                f"The {prefix} has already been loaded, ignoring previous value. Loading new with: '{file_name}'")

        # Opening JSON file
        f = open(file_name)
        self._hTable[prefix] = json.load(f)

    def getConfig(self, prefix):
        if not prefix in self._hTable:
            raise Exception(f"Value: '{prefix}' not found in the reg!")

        return self._hTable[prefix]
