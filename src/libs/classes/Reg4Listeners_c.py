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

    def addConfig(self, prefix, file_name=None, env_var_with_filename=None):
        Reg4Configs_m.Reg4Configs_c.getInstance().addConfig(
            prefix, file_name=file_name, env_var_with_filename=env_var_with_filename)

    def addListener(self, callable, prefix, topic, cmnd=None):
        self.__Listeners[prefix][topic][cmnd][callable] = 1

    def processEvent(self, prefix, topic, cmnd):
        h = Reg4Configs_m.Reg4Configs_c.getInstance().getConfig(prefix)

        if topic in h:
            # listeners notification
            [f(topic) for f in self.__Listeners[prefix][topic][None]]

            if cmnd in h[topic]:
                # command match processing
                [f(cmnd) for f in self.__Listeners[prefix][topic][cmnd]]

                # finally, event processing
                for v in h[topic][cmnd]:
                    pp, cc = v.split("|")
                    ret = self.mqtt_client.publish(pp, cc)
                    if ret.rc:
                            self.logging.warn(
                                f"Couldn't send message '{cc}' to '{pp}'")
                return True

        return False  # False means path not served, so can be handled by sth else
