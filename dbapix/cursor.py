import abc

import six

from .query import bind


@six.add_metaclass(abc.ABCMeta)
class Cursor(object):

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
        raw = self.wrapped.fetchone()
        if raw is not None:
            return self._engine.row_class(raw, self)

    def fetchall(self):
        rows = []
        while True:
            row = self.fetchone()
            if row is None:
                return rows
            rows.append(row)

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

        self._fields = []
        self._field_indexes = {}
        for i, field in enumerate(self.description or ()):
            self._fields.append(field[0])
            self._field_indexes[field[0]] = i

        return self

    def insert(self, table_name, data, returning=None):

        parts = ['INSERT INTO %s' % self._engine._quote_identifier(table_name)]

        names = []
        placeholders = []
        params = []

        for key, value in sorted(data.items()):
            names.append(self._engine._quote_identifier(key)) # TODO: Quote better.
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

        parts = ['UPDATE "%s"' % table_name]

        names = []
        values = []
        params = []

        to_set = []
        for key, value in sorted(data.items()):
            names.append('"%s"' % key) # TODO: Quote better.
            if isinstance(value, SQL):
                to_set.append('"%s" = %s' % (key, value))
            else:
                to_set.append('"%s" = %%s' % key)
                params.append(value)
        parts.append('SET %s' % ', '.join(to_set))

        parts.append('WHERE %s' % where)
        params.extend(where_params)

        query = ' '.join(parts)
        self.execute(query, params)

    def select(self, table_name, fields, where=None, where_params=()):

        parts = ['SELECT %s' % ', '.join(fields)]
        parts.append('FROM %s' % table_name)
        if where:
            parts.append('WHERE %s' % where)

        query = ' '.join(parts)
        self.execute(query, where_params)

        return self

    def as_dataframe(self, rows=None, **kwargs):
        import pandas
        if rows is None:
            rows = self.fetchall()
        kwargs.setdefault('columns', [f[0] for f in self.description])
        return pandas.DataFrame.from_records(rows, **kwargs)
    
