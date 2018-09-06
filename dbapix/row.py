import collections

from six import PY2, string_types


class Row(tuple):

    def __new__(cls, raw, *args):
        return super(Row, cls).__new__(cls, raw)

    def __init__(self, raw, fields):
        self._fields = fields
        self._field_names = None

    def __repr__(self):
        if self._field_names is None:
            self._field_names = {v: k for k, v in self._fields.items()}
        return '<Row {}>'.format(', '.join('{}={!r}'.format(self._field_names[i], v) for i, v in enumerate(self)))

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

    def iterkeys(self):
        return iter(self._fields)

    def keys(self):
        return self._fields.keys()

    def itervalues(self):
        return iter(self)

    def values(self):
        return list(self)

    def iteritems(self):
        for k in self._fields:
            yield k, self[k]

    def items(self):
        if PY2:
            return list(self.iteritems())
        else:
            return self.iteritems()

    def copy(self):
        return {k: self[k] for k in self.keys()}

