from __future__ import absolute_import

import MySQLdb

from six import string_types

from .pymysql import Engine as _Engine, Connection as _Connection


class Connection(_Connection):

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self._closed = False

    @property
    def closed(self):
        return self._closed

    def close(self):
        if not self._closed:
            self._closed = True
            self.wrapped.close()
    

class Engine(_Engine):

    connection_class = Connection

    def _connect(self, timeout):
        return MySQLdb.Connect(

            # read_timeout=timeout,
            # write_timeout=timeout,

            **self.connect_kwargs
        )
