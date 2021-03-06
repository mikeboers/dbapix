from __future__ import absolute_import

import MySQLdb

from dbapix.connection import Connection as _Connection
from dbapix.cursor import Cursor as _Cursor
from dbapix.engine import SocketEngine as _Engine


class Connection(_Connection):

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self._closed = False

    def fileno(self):
        return None
    
    @property
    def closed(self):
        return self._closed

    def close(self):
        if not self._closed:
            self._closed = True
            self.wrapped.close()
    
    def _can_disable_autocommit(self):
        # There really isn't a way we can tell, so... yeah.
        return True

    @property
    def autocommit(self):
        return self.wrapped.get_autocommit()

    @autocommit.setter
    def autocommit(self, value):
        # It is a method in the superclass.
        self.wrapped.autocommit(value)


class Engine(_Engine):

    paramstyle = 'format'
    placeholder = '%s'
    
    connection_class = Connection

    default_port = 3306
    
    def _connect(self, timeout):
        return MySQLdb.Connect(
            **self.connect_kwargs
        )

    def _connect_exc_is_timeout(self, e):
        pass
    
    @classmethod
    def quote_identifier(cls, name):
        return '`{}`'.format(name)

