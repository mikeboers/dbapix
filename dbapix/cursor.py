import abc

import six

from .query import bind, SQL
from .row import RowList


@six.add_metaclass(abc.ABCMeta)
class Cursor(object):

    """A database cursor, used to manage the context of a fetch operation.

    See `the DB-API 2.0 specs <https://www.python.org/dev/peps/pep-0249/#cursor-objects>`_
    for the full specifications. Here we will document the basics and notable differences.

    """

    def __init__(self, engine, raw):
        self._engine = engine
        self.wrapped = raw

    def __getattr__(self, key):
        return getattr(self.wrapped, key)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def fetchone(self):
        """Fetch the next row of a query result set.

        :return: A :class:`.Row`, or ``None`` when no more data is available.

        """
        raw = self.wrapped.fetchone()
        if raw is not None:
            return self._engine.row_class(raw, self)

    def fetchmany(self, size=None):
        """Fetch the next set of rows of a query result set.

        :param int size: Upper limit of rows to fetch; defaults to :attr:`Cursor.arraysize`.
        :return: A :class:`.RowList` of zero or more :class:`.Row`.

        """
        if size is None:
            size = self.arraysize
        rows = RowList(self)
        while len(rows) < size:
            row = self.fetchone()
            if row is None:
                break
            rows.append(row)
        return rows

    def fetchall(self):
        """Fetch all (remaining) rows of a query result set.

        :return: A :class:`.RowList` of zero or more :class:`.Row`.

        """
        rows = RowList(self)
        while True:
            row = self.fetchone()
            if row is None:
                break
            rows.append(row)
        return rows

    def __iter__(self):
        while True:
            row = self.fetchone()
            if row is None:
                return
            yield row

    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration()
        return row

    next = __next__

    def execute(self, query, params=None, _stack_depth=0):

        bound = bind(query, params, _stack_depth + 1)
        query, params = bound(self._engine)
        res = self.wrapped.execute(query, params)

        self._field_names = []
        self._field_indexes = {}
        for i, field in enumerate(self.description or ()):
            self._field_names.append(field[0])
            self._field_indexes[field[0]] = i

        return self

    def insert(self, table_name, data, returning=None):

        parts = ['INSERT INTO %s' % self._engine._quote_identifier(table_name)]

        names = []
        placeholders = []
        params = []

        for key, value in sorted(data.items()):
            names.append(self._engine._quote_identifier(key))
            placeholders.append('{}')
            params.append(value)

        parts.append('(%s) VALUES (%s)' % (
            ', '.join(names),
            ', '.join(placeholders),
        ))

        if returning:
            parts.append('RETURNING {}'.format(self._engine._quote_identifier(returning)))

        query = ' '.join(parts)
        self.execute(query, params)

        if returning:
            return next(self)[0]

    def update(self, table_name, data, where, where_params=()):

        values = []
        params = []

        to_set = []
        for key, value in sorted(data.items()):
            to_set.append('{} = {{}}'.format(self._engine._quote_identifier(key)))
            params.append(value)

        parts = [
            'UPDATE',
            self._engine._quote_identifier(table_name),
            'SET',
            ', '.join(to_set),
            'WHERE',
            where
        ]

        params.extend(where_params)

        query = ' '.join(parts)

        self.execute(query, params)

    def select(self, table_name, fields, where=None, where_params=()):

        parts = [
            'SELECT',
            ', '.join(x if x in ('*', ) else self._engine._quote_identifier(x) for x in fields),
            'FROM',
            self._engine._quote_identifier(table_name),
        ]

        if where:
            parts.append('WHERE')
            parts.append(where)

        query = ' '.join(parts)
        self.execute(query, where_params)

        return self

    def as_dataframe(self, rows=None, **kwargs):
        """Fetch all (remaining) rows as a ``pandas.DataFrame``.

        :param list rows: Manually picked rows to convert to a ``DataFrame``.
        :param \**kwargs: (e.g. ``index``, ``exclude``, ``coerce_float``)
            to pass to `pandas.DataFrame.from_records <https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.from_records.html>`_.
        
        :return: ``pandas.DataFrame``

        """

        # Gotta be careful to give it an actual list.
        if rows is None:
            rows = self.fetchall()

        # Pandas strictly requires specific types... or to be very generic.
        # We really don't know the performance impact of this.
        if type(rows) not in (tuple, list):
            rows = iter(rows)

        kwargs.setdefault('columns', [f[0] for f in self.description])

        import pandas
        return pandas.DataFrame.from_records(iter(rows), **kwargs)
    
