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
        )

class Connection(_ConnectionMixin, sqlite3.Connection):

    @property
    def closed(self):
        return False

    def cursor(self):
        return super(Connection, self).cursor(factory=Cursor)


class Cursor(_CursorMixin, sqlite3.Cursor):

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

