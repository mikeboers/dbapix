from __future__ import print_function

import collections

from six import PY2, string_types


class RowList(list):

    """An extension of ``list`` for holding rows."""

    def __init__(self, cur):
        self._field_names = cur._field_names

    def as_dataframe(self, **kwargs):
        """Convert these rows into a ``pandas.DataFrame``.

        See: :meth:`Cursor.as_dataframe`.

        """

        # This is essentially copy-pasta from the Cursor.as_dataframe.
        kwargs.setdefault('columns', self._field_names)
        import pandas
        return pandas.DataFrame.from_records(iter(self), **kwargs)

    def print_table(self):

        str_rows = [map(str, row) for row in self]

        max_lens = map(len, self._field_names)
        for row in str_rows:
            for i, x in enumerate(row):
                max_lens[i] = max(max_lens[i], len(x))

        pattern = ' | '.join('{{:{}s}}'.format(n) for n in max_lens)

        print(pattern.format(*self._field_names))
        print('-|-'.join('-' * x for x in max_lens))

        for row in str_rows:
            print(pattern.format(*row))

class Row(tuple):

    """A row in a query result.

    Rows are tuples, but they have been augmented to behave like dicts::

        for row in cur.execute('''SELECT foo FROM bar'''):
            print(row[0])
            print(row['foo']) # The same thing.

    **Warning:** checking if a string is in a row via ``'foo' in row`` will
    check for BOTH the key ``'foo'`` and the value ``'foo'``! If you need to be
    explicit, then you should look in the various views::

        'foo' in row.viewkeys()
        # of
        'foo' in row.viewvalues()

    """

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
    def viewkeys(self):
        return RowKeysView(self)

    def keys(self):
        if PY2:
            return self._field_names[:] # Don't want them changing it!
        else:
            return RowKeysView(self)

    def itervalues(self):
        return RowValuesView(self)
    def viewvalues(self):
        return RowValuesView(self)

    def values(self):
        if PY2:
            return list(self)
        else:
            return RowValuesView(self)

    def iteritems(self):
        return RowItemsView(self)
    def viewitems(self):
        return RowItemsView(self)

    def items(self):
        if PY2:
            return [(k, self[i]) for i, k in enumerate(self._field_names)]
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
        return x in self._row._field_indexes

class RowValuesView(_ViewMixin, collections.ValuesView):

    def __iter__(self):
        return iter(self._row)

    def __contains__(self, x):
        # This is nasty.
        return tuple.__contains__(self._row, x)

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

