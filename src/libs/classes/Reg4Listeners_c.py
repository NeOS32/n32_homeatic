from collections import deque
import libs.classes.Reg4Configs_c as Reg4Configs_m
import json


class Reg4Listeners_c:  # singletone
    __instance = None
    _persist_methods = ['get', 'save', 'delete', 'asdf']

    def __init__(self, mqtt_client, logging):
        """ Virtually private constructor. """
        if None != Reg4Listeners_c.__instance:
            raise Exception("This class is a singleton!")
        else:
            Reg4Listeners_c.__instance = self

        # other stuff
        self.mqtt_client = mqtt_client
        self.logging = logging

    @staticmethod
    def getInstance():
        """ Static access method. """
        if None == Reg4Listeners_c.__instance:
            Reg4Listeners_c()
        return Reg4Listeners_c.__instance

    def addConfig(self, prefix, file_name):
        Reg4Configs_m.Reg4Configs_c.getInstance().addConfig(prefix, file_name)

    def processEvent(self, prefix, topic, cmnd):
        if topic in self._hTable:
            if cmnd in self._hTable[topic]:
                for v in self._hTable[topic][cmnd]:
                    pp, cc = v.split("|")
                    ret = self.mqtt_client.publish(pp, cc)
                    if ret.rc:
                        self.logging.warn(
                            f"Couldn't send message '{cc}' to '{pp}'")
                return True

        return False  # False means path not served, so can be handled by sth else
