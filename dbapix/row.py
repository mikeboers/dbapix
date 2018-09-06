import collections

from six import PY2, string_types


class Row(tuple):

    def __new__(cls, raw, *args):
        return super(Row, cls).__new__(cls, raw)

    def __init__(self, raw, cur):
        # We need to copy these stuff over so that if/when the cursor changes,
        # these don't. All the rows will share the same collections, so there
        # isn't a big memory drain.
        self._field_indexes = cur._field_indexes
        self._field_names = cur._field_names

    def __repr__(self):
        return '<Row {}>'.format(', '.join('{}={!r}'.format(self._field_names[i], v) for i, v in enumerate(self)))

    def __getitem__(self, x):
        if isinstance(x, string_types):
            x = self._field_indexes[x]
        return super(Row, self).__getitem__(x)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, x):
        if x in self._field_indexes:
            return True
        return super(Row, self).__contains__(x)

    def iterkeys(self):
        return RowKeysView(self)

    def keys(self):
        if PY2:
            return self._field_names[:] # Don't want them changing it!
        else:
            return RowKeysView(self)

    def itervalues(self):
        return RowValuesView(self)

    def values(self):
        if PY2:
            return list(self)
        else:
            return RowValuesView(self)

    def iteritems(self):
        return RowItemsView(self)

    def items(self):
        if PY2:
            return list(RowItemsView(self))
        else:
            return RowItemsView(self)

    def copy(self):
        return {k: self[k] for k in self.keys()}


class _ViewMixin(object):

    def __init__(self, row):
        self._row = row

    def __len__(self):
        return len(self._row)

class RowKeysView(_ViewMixin, collections.KeysView):

    def __iter__(self):
        return iter(self._row._field_names)

    def __contains__(self, x):
        return x in self._row

class RowValuesView(_ViewMixin, collections.ValuesView):

    def __iter__(self):
        return iter(self._row)

    def __contains__(self, x):
        return x in self._row

class RowItemsView(_ViewMixin, collections.ItemsView):

    def __iter__(self):
        for k in self._row._field_names:
            yield k, self._row[k]

    def __contains__(self, x):
        if not isinstance(x, tuple) or len(x) != 2:
            return False
        k, v = x
        try:
            return self._row[k] == v
        except (IndexError, KeyError):
            return False

