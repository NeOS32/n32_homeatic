from datetime import datetime


class var_c:
    def __init__(self, name, event_class, location=None, gramma=None, debug=False, default_value=0):
        self._hTable = {
            "name": name,
            "event_class": event_class,
            "location": location,
            "gramma": gramma,
            "value": default_value,
            "last_updated": None,
            "debug": debug}

    def __repr__(self):
        return f'Nma: {self.name}, class: {self.get_event_class}, location: {self.location}, value: {self.default_value},'

    def get_name(self):
        return self._hTable['name']

    def get_value(self):
        return self._hTable['value']

    def get_gramma(self):
        return self._hTable['gramma']

    def get_debug(self):
        return self._hTable['debug']

    def get_location(self):
        return self._hTable['location']

    def get_event_class(self):
        return self._hTable['event_class']

    def set_value(self, value):
        self._hTable['last_updated'] = datetime.now()
        self._hTable['value'] = value

    def get_last_updated(self):
        return self._hTable['last_updated']

    def add_to_value(self, new_value):
        self.set_value(new_value)

        return self._hTable['value']

    # def __getattr__(self, attribute):
        # if attribute in self._persist_methods:
        #   return getattr(self._persister, attribute)
