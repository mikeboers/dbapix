from six import string_types


class Row(tuple):

    def __new__(cls, raw, *args):
        return super(Row, cls).__new__(cls, raw)

    def __init__(self, raw, fields):
        self._fields = fields

    def __getitem__(self, x):
        if isinstance(x, string_types):
            x = self._fields[x]
        return super(Row, self).__getitem__(x)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        try:
            self[key]
            return True
        except (IndexError, KeyError):
            return False

    def keys(self):
        return self._fields.keys()

    def copy(self):
        return {k: self[k] for k in self.keys()}

    # TODO: More of the dict methods!