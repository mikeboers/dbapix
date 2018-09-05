

class Row(tuple):

    @classmethod
    def _wrap(cls, cur, raw):
        self = cls(raw)
        #self._fields = fields
        return self

    def __getitem__(self, x):
        if isinstance(x, basestring):
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