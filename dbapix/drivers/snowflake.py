from __future__ import absolute_import

import snowflake.connector

from six import string_types

from dbapix.connection import Connection as _Connection
from dbapix.engine import Engine as _Engine


class Connection(_Connection):
    
    def _can_disable_autocommit(self):
        return True

    def fileno(self):
        return None


class Engine(_Engine):

    connection_class = Connection
    
    paramstyle = 'qmark'
    placeholder = '?'

    def __init__(self, **kwargs):
        super(Engine, self).__init__()
        self.connect_kwargs = kwargs

    def _connect(self, timeout):
        con = snowflake.connector.connect(**self.connect_kwargs)
        con.paramstyle = 'qmark'
        return con

    def _connect_exc_is_timeout(self, exc):
        pass
