import libs.classes.Reg4Configs_c as Reg4Configs_m
from time import sleep


class autovivification_c(dict):
    """ Helper class for perl-like autovivification. Based on impl from SO """

    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


class Reg4Listeners_c:  # singletone
    """ A registry for MQTT listeners """
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
        self.__Listeners = autovivification_c()

    @staticmethod
    def getInstance():
        """ Static access method. """
        if None == Reg4Listeners_c.__instance:
            Reg4Listeners_c()
        return Reg4Listeners_c.__instance

    def addConfig(self, file_name=None, env_var_with_filename=None):
        Reg4Configs_m.Reg4Configs_c.getInstance().addConfig(
            file_name=file_name, env_var_with_filename=env_var_with_filename)

    def getListenersHash(self, prefixes, force_creation=False):
        h = self.__Listeners
        keyword = None
        index = 0

        while index < len(prefixes):
            keyword = prefixes[index]  # getting an element from given index
            if False == force_creation and keyword not in h:
                return None
            h = h[keyword]
            index += 1

        return h

    def addListener(self, prefixes, callable):
        # _semConfigs.acquire()

        h = self.getListenersHash(prefixes, force_creation=True)
        h[callable] = 1

        # _semConfigs.release()

    # processes events declared both:
    #  - in external jsons
    #  - in source code in a form of listener
    def processEvent(self, prefixes):
        # listeners first (source code)
        H = self.getListenersHash(prefixes)
        if H:
            [f() for f in H]

        # actions second (jsons),but only when we have level > 1 (means path and value)
        if len(prefixes) > 1:
            for v in Reg4Configs_m.Reg4Configs_c.getInstance().getConfigYield(prefixes):
                pp, cc = v.split("|")
                ret = self.mqtt_client.publish(pp, cc)
                if ret.rc:
                    self.logging.warn(
                        f"Couldn't send message '{cc}' to '{pp}'")
