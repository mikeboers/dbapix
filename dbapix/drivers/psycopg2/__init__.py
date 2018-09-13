from __future__ import absolute_import

import psycopg2 as pg
import psycopg2.extensions as pgx
import psycopg2.extras
import six

from dbapix.connection import Connection as _Connection
from dbapix.cursor import Cursor as _Cursor
from dbapix.engine import Engine as _Engine
from dbapix.query import SQL



# This is setting up global state, but it is with our own class,
# so it shouldn't affect anyone else.
pgx.register_adapter(SQL, pgx.AsIs)


_status_names = {
    pgx.TRANSACTION_STATUS_IDLE: 'IDLE',
    pgx.TRANSACTION_STATUS_ACTIVE: 'ACTIVE',
    pgx.TRANSACTION_STATUS_INTRANS: 'INTRANS',
    pgx.TRANSACTION_STATUS_INERROR: 'INERROR',
    pgx.TRANSACTION_STATUS_UNKNOWN: 'UNKNOWN',
}


class Connection(_Connection):

    def _can_disable_autocommit(self):
        return self.wrapped.get_transaction_status() == pgx.TRANSACTION_STATUS_IDLE

    def _should_put_close(self):
        return self.wrapped.get_transaction_status() in (pgx.TRANSACTION_STATUS_UNKNOWN, )

    def _get_nonidle_status(self):
        status = self.wrapped.get_transaction_status()
        if status != pgx.TRANSACTION_STATUS_IDLE:
            return _status_names.get(status, status)


class Engine(_Engine):

    connection_class = Connection
    
    paramstyle = 'format'
    placeholder = '%s'
    
    def __init__(self, connect_kwargs):
        super(Engine, self).__init__()
        self.connect_kwargs = connect_kwargs

    def _reset_session(self, autocommit=False):
        self.wrapped.set_session(
            isolation_level='DEFAULT',
            readonly=False,
            deferrable=False,
            autocommit=autocommit
        )

    def _connect(self, timeout):
        return pg.connect(
            **self.connect_kwargs
        )

    def _connect_exc_is_timeout(self, e):
        return (
            isinstance(e, pg.OperationalError) and
            any(x in e.args[0] for x in ('could not connect', 'starting up', 'shutting down'))
        )





