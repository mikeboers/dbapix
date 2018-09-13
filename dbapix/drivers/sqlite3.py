from __future__ import absolute_import

import sqlite3

from six import string_types

from dbapix.connection import Connection as _Connection
from dbapix.engine import Engine as _Engine


class Connection(_Connection):

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self._isolation_level = None
        self._closed = False

    def fileno(self):
        return None
    
    @property
    def closed(self):
        return self._closed

    def close(self):
        self.wrapped.close()
        self._closed = True

    def _can_disable_autocommit(self):
        # There really isn't a way we can tell, so... yeah.
        return True

    @property
    def autocommit(self):
        # In Python's sqlite3 autocommit is tied to the isolation level.
        return self.wrapped.isolation_level is None

    @autocommit.setter
    def autocommit(self, value):

        if value and self.isolation_level is not None:
            self._isolation_level = self.wrapped.isolation_level
            self.wrapped.isolation_level = None

        elif not value and self.isolation_level is None:
            self.wrapped.isolation_level = self._isolation_level or ''
            self._isolation_level = None


class Engine(_Engine):

    connection_class = Connection
    
    paramstyle = 'qmark'
    placeholder = '?'

    _types = {'serial primary key': 'INTEGER PRIMARY KEY'}

    def __init__(self, path):
        super(Engine, self).__init__()
        self.path = path

    def _connect(self, timeout):
        return sqlite3.connect(self.path,
            timeout=timeout or 0,
        )

    def _connect_exc_is_timeout(self, e):
        return False


