import logging
import sys
import time
import weakref

import psycopg2 as pg
import psycopg2.extensions as pgx
import psycopg2.extras


log = logging.getLogger()


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


class Engine(object):

    def __init__(self, connect_kwargs):

        self.connect_kwargs = connect_kwargs

        self.pool = []
        self.max_idle = 2
        self._context_refs = {}

    def get_connection(self, autocommit=False, timeout=None):
        
        try:
            con = self.pool.pop(0)
        except IndexError:
            con = self._connect(timeout)

        # Store where it came from so we can warn later.
        frame = sys._getframe(1)
        con._origin = (frame.f_code.co_filename, frame.f_lineno)

        # Reset the session to a reasonable default.
        con.set_session(
            isolation_level='DEFAULT',
            readonly=False,
            deferrable=False,
            autocommit=autocommit
        )

        return con

    def _connect(self, timeout):
        start = time.time()
        delay = 0.1
        while True:
            try:
                return pg.connect(
                    connection_factory=Connection,
                    cursor_factory=Cursor,
                    **self.connect_kwargs
                )
            except pg.OperationalError as e:
                if timeout is None:
                    raise
                if not any(x in e.args[0] for x in ('could not connect', 'starting up', 'shutting down')):
                    raise
                if time.time() - start >= timeout:
                    raise e
            time.sleep(delay)
            delay *= 1.41

    def put_connection(self, con, close=False, warn_status=True):

        if con.closed:
            return

        close = close or len(self.pool) >= self.max_idle
        status = con.get_transaction_status()

        if status == pgx.TRANSACTION_STATUS_UNKNOWN:
            con.close()
            return

        if status != pgx.TRANSACTION_STATUS_IDLE:
            if warn_status:
                log.warning("Connection from {0[0]}:{0[1]} returned with non-idle status {1}.".format(
                    con._origin,
                    _status_names.get(status, status),
                ))
            if not close:
                con.rollback()

        if close:
            con.close
            return

        if con not in self.pool:
            self.pool.append(con)

    def _build_context(self, con, obj):
        ctx = ConnectionContext(self, con, obj)
        # Use weakrefs to trigger returning the connection to avoid __del__.
        ref = weakref.ref(ctx, self._context_destructed)
        self._context_refs[ref] = con
        return ctx

    def _context_destructed(self, ref):
        con = self._context_refs.pop(ref)
        self.put_connection(con)

    def connect(self, *args, **kwargs):
        con = self.get_connection(*args, **kwargs)
        return self._build_context(con, con)

    def cursor(self, *args, **kwargs):
        con = self.get_connection(*args, **kwargs)
        cur = con.cursor()
        return self._build_context(con, cur)

    def execute(self, *args, **kwargs):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(*args, **kwargs)
        return self._build_context(con, cur)





class ConnectionContext(object):

    """Context manager for returning connections back to the pool.

    Note that this is not a proxy for the object; You need to use this
    as a context manager to get the object.

    """

    def __init__(self, db, con, obj):
        self._db = db
        self._con = con
        self._obj = obj

    def __repr__(self):
        if self._con is self._obj:
            return '<ConnectionContext con={}>'.format(self._con)
        else:
            return '<ConnectionContext con={} obj={}>'.format(self._con, self.obj)

    def put_connection(self, *args, **kwargs):
        if self._con is not None:
            self._db.put_connection(self._con, *args, **kwargs)
            self._con = None
    
    def __enter__(self):
        return self._obj

    def __exit__(self, *args):
        self.put_connection()


class TransactionContext(object):

    def __init__(self, con):
        self._con = con

    def __enter__(self):
        return self._con

    def __exit__(self, exc_type=None, *args):
        if exc_type:
            self._con.rollback()
        else:
            self._con.commit()

    def __getattr__(self, key):
        return getattr(self._con, key)


class Connection(pgx.connection):

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self._autocommit = None

    def begin(self):
        
        # Optimize to use the included methods if we can. We will drop back
        # into autocommit mode later.
        if self.autocommit and self.get_transaction_status() == pgx.TRANSACTION_STATUS_IDLE:
            self._autocommit = True
            self.autocommit = False

        if self.autocommit:
            self.cursor().execute('BEGIN')
        else:
            self.__enter__()

        return TransactionContext(self)

    def _end(self):
        if self._autocommit is not None:
            self.autocommit = self._autocommit
            self._autocommit = None

    def commit(self):
        if self.autocommit:
            raise RuntimeError("Connection is in autocommit mode.")
        super(Connection, self).commit()
        self._end()

    def rollback(self):
        if self.autocommit:
            raise RuntimeError("Connection is in autocommit mode.")
        super(Connection, self).rollback()
        self._end()

    def execute(self, *args, **kwargs):
        # No cursor context here since it needs to be read.
        cur = self.cursor()
        cur.execute(*args, **kwargs)
        return cur

    def select(self, *args, **kwargs):
        # No cursor context here since it needs to be read.
        cur = self.cursor()
        return cur.select(*args, **kwargs)

    def insert(self, *args, **kwargs):
        with self.cursor() as cur:
            return cur.insert(*args, **kwargs)

    def update(self, *args, **kwargs):
        with self.cursor() as cur:
            return cur.update(*args, **kwargs)


class Cursor(pg.extras.DictCursor):

    def insert(self, table_name, data, returning=None):

        parts = ['INSERT INTO "%s"' % table_name] # TODO: Quote better.

        names = []
        placeholders = []
        params = []

        for key, value in sorted(data.items()):
            names.append('"%s"' % key) # TODO: Quote better.
            placeholders.append('%s')
            params.append(value)

        parts.append('(%s) VALUES (%s)' % (
            ', '.join(names),
            ', '.join(placeholders),
        ))

        if returning:
            parts.append('RETURNING "%s"' % returning) # TODO: Quote better.

        query = ' '.join(parts)
        self.execute(query, params)

        if returning:
            return next(self)[0]

    def update(self, table_name, data, where, where_params=()):

        parts = ['UPDATE "%s"' % table_name]

        names = []
        values = []
        params = []

        to_set = []
        for key, value in sorted(data.items()):
            names.append('"%s"' % key) # TODO: Quote better.
            if isinstance(value, SQL):
                to_set.append('"%s" = %s' % (key, value))
            else:
                to_set.append('"%s" = %%s' % key)
                params.append(value)
        parts.append('SET %s' % ', '.join(to_set))

        parts.append('WHERE %s' % where)
        params.extend(where_params)

        query = ' '.join(parts)
        self.execute(query, params)

    def select(self, table_name, fields, where=None, where_params=()):

        parts = ['SELECT %s' % ', '.join(fields)]
        parts.append('FROM %s' % table_name)
        if where:
            parts.append('WHERE %s' % where)

        query = ' '.join(parts)
        self.execute(query, where_params)

        return self


