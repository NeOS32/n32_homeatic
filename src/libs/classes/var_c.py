from datetime import datetime


class var_c:
    def __init__(self, name, event_class, location=None, gramma="MajorQuant", debug=False, default_value=0, regex=None):
        self._hTable = {
            "name": name,
            "event_class": event_class,
            "location": location,
            "gramma": gramma,
            "value": default_value,
            "last_updated": None,
            "debug": debug,
            "regex": regex
        }

    def __repr__(self):
        return f'Nma: {self.name}, class: {self.get_event_class}, location: {self.location}, value: {self.default_value},'

    def get_key(self, key):
        return self._hTable.get(key)

    def get_name(self):
        return self.get_key('name')

    def get_value(self):
        return self.get_key('value')

    def get_gramma(self):
        return self.get_key('gramma')

    def get_debug(self):
        return self.get_key('debug')

    def get_location(self):
        return self.get_key('location')

    def get_event_class(self):
        return self.get_key('event_class')

    def get_last_updated(self):
        return self.get_key('last_updated')

    def set_value(self, value):
        self._hTable['last_updated'] = datetime.now()
        self._hTable['value'] = value

    # def add_to_value(self, new_value):
    #     self.set_value(new_value)

    #     return self._hTable['value']

    # def __getattr__(self, attribute):
        # if attribute in self._persist_methods:
        #   return getattr(self._persister, attribute)
