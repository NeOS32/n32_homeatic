from collections import defaultdict
import json
import os
import threading

_semConfigs = threading.BoundedSemaphore(value=1)


class Reg4Configs_c(object):  # singletone
    __instance = None
    _persist_methods = ['get', 'save', 'delete', 'asdf']

    @staticmethod
    def getInstance():
        """ Static access method. """

        _semConfigs.acquire()
        if None == Reg4Configs_c.__instance:
            Reg4Configs_c.__instance = Reg4Configs_c()
        _semConfigs.release()

        return Reg4Configs_c.__instance

    def __init__(self):
        """ Virtually private constructor """

        # singleton stuff
        if None != Reg4Configs_c.__instance:
            raise Exception("This class is a singleton!")
        else:
            Reg4Configs_c.__instance = self

        # other stuff
        self._hTable = defaultdict(dict)

    def addConfig(self, extra_namespace=None, file_name=None, env_var_with_filename=None):
        _semConfigs.acquire()

        if file_name:
            # loading a JSON file
            f = open(file_name)
            j = json.load(f)

            h = self._hTable
            if extra_namespace:
                h = h[extra_namespace]

            # check for posible keys duplication
            if h:
                for k in j.keys():
                    if k in h:
                        _semConfigs.release()
                        raise Exception(
                            f"Key: '{k}' has already been defined!")

            # hash update
            h.update(j)

            _semConfigs.release()
            return

        elif env_var_with_filename:
            env_file_name = os.environ.get(env_var_with_filename)
            if env_file_name:

                _semConfigs.release()

                self.addConfig(
                    extra_namespace=extra_namespace, file_name=env_file_name)
                return

        _semConfigs.release()

        raise Exception(
            f"Value: At least one of arguments (file_name or env_var_with_filename) must be defined!")

    def getConfigYield(self, prefixes):
        keyword = None
        index = 0
        
        _semConfigs.acquire()

        h = self._hTable

        while h and index < len(prefixes):
            keyword = prefixes[index]  # using 'index' element
            if keyword not in h:
                
                _semConfigs.release()
                return None

            h = h[keyword]
            index += 1

        if isinstance(h, dict):
            for i in h.keys():
                yield i, h[i]  # yielding key/value pairs
        elif isinstance(h, list):
            for i in h:
                yield i  # yielding key/None pairs, to keep the same interface
        else:
            _semConfigs.release()
            raise Exception(
                f"Not supported type in reg4configs yielding!")

        _semConfigs.release()
