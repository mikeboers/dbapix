from __future__ import absolute_import

import pymysql

from six import string_types

from dbapix.connection import ConnectionMixin as _ConnectionMixin
from dbapix.cursor import CursorMixin as _CursorMixin
from dbapix.engine import Engine as _Engine


class Engine(_Engine):

    _paramstyle = 'format'

    def __init__(self, connect_kwargs):
        super(Engine, self).__init__()
        self.connect_kwargs = connect_kwargs

    def _connect(self, timeout):
        return Connection(
            
            # Stop it from calling the autocommit method, which we have
            # replaced with a property. This is very bad smelling. We should
            # be wrapping the connection, not doing this sort of thing.
            autocommit=None,

            cursorclass=Cursor,
            read_timeout=timeout,
            write_timeout=timeout,

            **self.connect_kwargs
        )

    def _prepare_connection(self, con, autocommit=False):
        con.autocommit = autocommit

    @classmethod
    def _quote_identifier(cls, name):
        return '`{}`'.format(name)

class Connection(_ConnectionMixin, pymysql.connections.Connection):

    # def __init__(self, *args, **kwargs):
    #     super(Connection, self).__init__(*args, **kwargs)        

    @property
    def closed(self):
        return self._closed

    def _can_disable_autocommit(self):
        # There really isn't a way we can tell, so... yeah.
        return True

    @property
    def autocommit(self):
        return self.get_autocommit()

    @autocommit.setter
    def autocommit(self, value):
        # It is a method in the superclass.
        super(Connection, self).autocommit(value)
    
    


class Cursor(_CursorMixin, pymysql.cursors.Cursor):

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __next__(self):
        return self.fetchone()

    next = __next__

    def _do_get_result(self):
        super(Cursor, self)._do_get_result()
        fields = {}
        if self.description:
            for i, f in enumerate(self._result.fields):
                fields[f.name] = i
        if fields and self._rows:
            self._rows = [Row._create(raw, fields) for raw in self._rows]

    def _conv_row(self, row):
        return row

