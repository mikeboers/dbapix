from __future__ import absolute_import

import sqlite3

from dbapix.connection import ConnectionMixin as _ConnectionMixin
from dbapix.cursor import CursorMixin as _CursorMixin
from dbapix.engine import Engine as _Engine


class Engine(_Engine):

    _paramstyle = 'qmark'
    _types = {'serial primary key': 'INTEGER PRIMARY KEY'}

    def __init__(self, path):
        super(Engine, self).__init__()
        self.path = path

    def _connect(self):
        return sqlite3.connect(self.path,
            factory=Connection,
            timeout=0,
        )

class Connection(_ConnectionMixin, sqlite3.Connection):

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self.row_factory = sqlite3.Row # Dict-ish behaviour.
        self._isolation_level = None

    @property
    def closed(self):
        return False

    def cursor(self):
        return super(Connection, self).cursor(factory=Cursor)

    @property
    def autocommit(self):
        return self.isolation_level is None

    @autocommit.setter
    def autocommit(self, value):
        
        if value and self.isolation_level is not None:
            self._isolation_level = self.isolation_level
            self.isolation_level = None

        elif not value and self.isolation_level is None:
            self.isolation_level = self._isolation_level or ''
            self._isolation_level = None
    


class Cursor(_CursorMixin, sqlite3.Cursor):

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

