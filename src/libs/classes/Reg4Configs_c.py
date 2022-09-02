from collections import defaultdict
import json
import os

import libs.classes.Synchro_c as Synchro_m


class Reg4Configs_c(object):  # singletone
    __instance = None
    _persist_methods = ['get', 'save', 'delete', 'asdf']
    _lock = Synchro_m.Synchro_c()

    def __init__(self):
        """ Virtually private constructor """

        # singleton stuff
        if None != Reg4Configs_c.__instance:
            raise Exception("This class is a singleton!")
        else:
            Reg4Configs_c.__instance = self

        # other stuff
        self._hTable = defaultdict(dict)

    @staticmethod
    def getInstance():
        """ Static access method. """

        with Reg4Configs_c._lock:
            if None == Reg4Configs_c.__instance:
                Reg4Configs_c()

        return Reg4Configs_c.__instance

    def addConfig(self, extra_namespace=None, file_name=None, env_var_with_filename=None):
        if file_name:
            # loading a JSON file
            f = open(file_name)
            j = json.load(f)

            with self._lock:
                h = self._hTable
                if extra_namespace:
                    h = h[extra_namespace]

                # check for posible keys duplicates
                if h:
                    for k in j.keys():
                        if k in h:
                            raise Exception(
                                f"Key: '{k}' has already been defined!")
                # hash update
                h.update(j)
                return
        elif env_var_with_filename:
            env_file_name = os.environ.get(env_var_with_filename)
            if env_file_name:
                self.addConfig(
                    extra_namespace=extra_namespace, file_name=env_file_name)
                return
        raise Exception(
            f"Value: At least one of arguments (file_name or env_var_with_filename) must be defined!")

    def getConfigYield(self, prefixes):
        keyword = None
        index = 0

        with self._lock:
            h = self._hTable

            while h and index < len(prefixes):
                keyword = prefixes[index]  # using 'index' element
                if keyword not in h:
                    return None
                h = h[keyword]
                index += 1

            if isinstance(h, dict):
                for i in h.keys():
                    yield i, h[i]  # yielding key/value pairs
            elif isinstance(h, list):
                for i in h:
                    yield i  # yielding key, to keep the same interface
            else:
                raise Exception(
                    f"Not supported type in reg4configs yielding!")
