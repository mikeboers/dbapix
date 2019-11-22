from __future__ import absolute_import

import ctds

from dbapix.connection import Connection as _Connection
from dbapix.cursor import Cursor as _Cursor
from dbapix.engine import SocketEngine as _Engine


class Connection(_Connection):

    def fileno(self):
        pass

    @property
    def closed(self):
        return self.wrapped.database is None
    
    def _can_disable_autocommit(self):
        return True

    

class Engine(_Engine):

    paramstyle = 'numeric'
    placeholder = ':0'

    connection_class = Connection

    default_port = 1433

    _types = {
        'serial primary key': 'INTEGER IDENTITY PRIMARY KEY',
        'serial': 'INTEGER IDENTITY',
    }

    def _connect(self, timeout):
        return ctds.connect(
            **self.connect_kwargs
        )

    def _connect_exc_is_timeout(self, e):
        pass

    @classmethod
    def quote_identifier(cls, name):
       return '[{}]'.format(name)



