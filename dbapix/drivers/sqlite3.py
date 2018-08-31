from __future__ import absolute_import

import sqlite3

from six import string_types

from dbapix.connection import ConnectionMixin as _ConnectionMixin
from dbapix.cursor import CursorMixin as _CursorMixin
from dbapix.engine import Engine as _Engine


class Engine(_Engine):

    _paramstyle = 'qmark'
    _types = {'serial primary key': 'INTEGER PRIMARY KEY'}

    def __init__(self, path):
        super(Engine, self).__init__()
        self.path = path

    def _connect(self, timeout):
        return sqlite3.connect(self.path,
            factory=Connection,
            timeout=timeout or 0,
        )

class Connection(_ConnectionMixin, sqlite3.Connection):

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self.row_factory = Row # Dict-ish behaviour.
        self._isolation_level = None
        self._closed = False

    @property
    def closed(self):
        return self._closed

    def close(self):
        super(Connection, self).close()
        self._closed = True

    def _can_disable_autocommit(self):
        # There really isn't a way we can tell, so... yeah.
        return True

    def cursor(self):
        return super(Connection, self).cursor(factory=Cursor)

    @property
    def autocommit(self):
        # In Python's sqlite3 autocommit is tied to the isolation level.
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


class Row(sqlite3.Row):

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        try:
            return super(Row, self).__getitem__(key)
        except IndexError:
            if isinstance(key, string_types):
                raise KeyError(key)
            else:
                raise

    def __contains__(self, key):
        try:
            self[key]
            return True
        except (IndexError, KeyError):
            return False

    def copy(self):
        return {k: self[k] for k in self.keys()}

