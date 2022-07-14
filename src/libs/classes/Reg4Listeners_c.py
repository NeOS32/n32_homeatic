from collections import deque
from libs.classes.Event_c import Inputs, Outputs
import json


class Reg4Listeners_c:  # singletone
    __instance = None
    _persist_methods = ['get', 'save', 'delete', 'asdf']

    def __init__(self, mqtt_client,logging):
        """ Virtually private constructor. """
        self.mqtt_client = mqtt_client
        self.logging= logging

    @staticmethod
    def getInstance():
        """ Static access method. """
        if self.__instance == None:
            Reg4Listeners_c()
        return self.__instance

    def addConfig(self, file_name):
        # Opening JSON file
        f = open(file_name)

        # reading a JSON
        self._hTable = json.load(f)
        # TODO: mergin other JSONs

    def processEvent(self, topic, cmnd):
        if topic in self._hTable:
            if cmnd in self._hTable[topic]:
                for v in self._hTable[topic][cmnd]:
                    pp, cc = v.split("|")
                    ret = self.mqtt_client.publish(pp, cc)
                    if ret.rc:
                        self.logging.warn(f"Couldn't send message '{cc}' to '{pp}'")
                return True

        return False # False means path not served, so can be handled by sth else
