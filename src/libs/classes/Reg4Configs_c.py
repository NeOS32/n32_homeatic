from collections import defaultdict
import json
import os


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
        self._hTable = defaultdict(dict)

    def addConfig(self, prefix, file_name=None, env_var_with_filename=None):
        if file_name:
            # reading a JSON
            if prefix in self._hTable:
                self.logging.warn(
                    f"The {prefix} has already been loaded, ignoring previous value. Loading new with: '{file_name}'")

            # Opening JSON file
            f = open(file_name)
            self._hTable[prefix] = json.load(f)

            return

        elif env_var_with_filename:
            env_file_name = os.environ.get(env_var_with_filename)
            if env_file_name:
                self.addConfig(prefix, file_name=env_file_name)
                return

        raise Exception(
            f"Value: 'At least one of arguments (file_name or env_var_with_filename) must be defined!")

    def getConfig(self, prefix):
        if not prefix in self._hTable:
            raise Exception(f"Value: '{prefix}' not found in the reg!")

        return self._hTable[prefix]
