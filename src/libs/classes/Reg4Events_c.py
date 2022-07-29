from collections import deque
from libs.classes.Event_c import Inputs, Outputs


class Reg4Events_c:  # singletone
    __instance = None
    _persist_methods = ['get', 'save', 'delete', 'asdf']

    def __init__(self, events_in_table=100):
        """ Virtually private constructor. """
        if None != self.__instance:
            raise Exception("This class is a singleton!")
        else:
            self.__instance = self
            self.events_in_table = events_in_table
            self._hTable = {}
            self._hTracking = {}
            self._Events = deque(maxlen=events_in_table)

    @staticmethod
    def getInstance():
        """ Static access method. """
        if self.__instance == None:
            Reg4Events_c()
        return self.__instance

    def getEventVector(self, var):
        pass

    def getInputsCorpus(self):
        return [i for i in Inputs]

    def getOutputCorpus(self):
        return [i for i in Outputs]

    def add_event(self, var):
        V = self.getEventVector(var)
        # self._Events.append(var)
