from __future__ import absolute_import

import psycopg2 as pg
import psycopg2.extensions as pgx
import psycopg2.extras

from dbapix.connection import ConnectionMixin as _ConnectionMixin
from dbapix.cursor import CursorMixin as _CursorMixin
from dbapix.engine import Engine as _Engine


class SQL(str):
    """Literal SQL"""
    pass


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


class Engine(_Engine):

    _paramstyle = 'format'
    
    def __init__(self, connect_kwargs):
        super(Engine, self).__init__()
        self.connect_kwargs = connect_kwargs

    def _prepare_connection(self, con, autocommit=False):
        # Reset the session to a reasonable default.
        con.set_session(
            isolation_level='DEFAULT',
            readonly=False,
            deferrable=False,
            autocommit=autocommit
        )

    def _connect(self):
        return pg.connect(
            connection_factory=Connection,
            cursor_factory=Cursor,
            **self.connect_kwargs
        )

    def _connect_exc_is_timeout(self, e):
        return (
            isinstance(e, pg.OperationalError) and
            any(x in e.args[0] for x in ('could not connect', 'starting up', 'shutting down'))
        )

    def _should_put_close(self, con):
        return con.get_transaction_status() in (pgx.TRANSACTION_STATUS_UNKNOWN, )

    def _get_nonidle_status(self, con):
        status = con.get_transaction_status()
        if status != pgx.TRANSACTION_STATUS_IDLE:
            return _status_names.get(status, status)


class Connection(_ConnectionMixin, pgx.connection):

    def _can_disable_autocommit(self):
        return self.get_transaction_status() == pgx.TRANSACTION_STATUS_IDLE



class Cursor(_CursorMixin, pg.extras.DictCursor):

    pass



