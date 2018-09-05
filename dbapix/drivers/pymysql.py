from __future__ import absolute_import

import pymysql

from six import string_types

from dbapix.connection import Connection as _Connection
from dbapix.cursor import Cursor as _Cursor
from dbapix.engine import Engine as _Engine


class Connection(_Connection):

    @property
    def closed(self):
        return self.wrapped._closed

    def close(self):
        if not self.wrapped._closed:
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

    _paramstyle = 'format'

    connection_class = Connection

    def __init__(self, connect_kwargs):
        super(Engine, self).__init__()
        self.connect_kwargs = connect_kwargs

    def _connect(self, timeout):
        return pymysql.Connect(

            # read_timeout=timeout,
            # write_timeout=timeout,

            **self.connect_kwargs
        )

    def _connect_exc_is_timeout(self, e):
        pass

    @classmethod
    def _quote_identifier(cls, name):
        return '`{}`'.format(name)


