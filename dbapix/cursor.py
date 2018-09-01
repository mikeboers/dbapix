
from .query import bind


class CursorMixin(object):

    def execute(self, query, params=None, _stack_depth=0):
        bound = bind(query, params, _stack_depth + 1)
        query, params = bound(self._engine)
        # print(query, params)
        return super(CursorMixin, self).execute(query, params)

    def insert(self, table_name, data, returning=None):

        parts = ['INSERT INTO "%s"' % table_name] # TODO: Quote better.

        names = []
        placeholders = []
        params = []

        for key, value in sorted(data.items()):
            names.append('"%s"' % key) # TODO: Quote better.
            placeholders.append('{}')
            params.append(value)

        parts.append('(%s) VALUES (%s)' % (
            ', '.join(names),
            ', '.join(placeholders),
        ))

        if returning:
            parts.append('RETURNING "{}"' % returning) # TODO: Quote better.

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
