import logging
import sys
import time
import weakref
import re

log = logging.getLogger()

from .query import bind as bind_query


class Engine(object):

    def __init__(self):
        self.pool = []
        self.max_idle = 2
        self._checked_out = []
        self._context_refs = {}

    def close(self):
        for collection in (self.pool, self._checked_out):
            while collection:
                collection.pop().close()

    def __del__(self):
        self.close()

    def get_connection(self, timeout=None, **kwargs):
        
        try:
            con = self.pool.pop(0)
        except IndexError:
            con = self._new_connection(timeout)
            con._engine = self

        # Store where it came from so we can warn later.
        frame = sys._getframe(1)
        con._origin = (frame.f_code.co_filename, frame.f_lineno)

        self._prepare_connection(con, **kwargs)
        self._checked_out.append(con)

        return con

    def _prepare_connection(self, con, **kwargs):
        pass

    def _new_connection(self, timeout):
        start = time.time()
        delay = 0.1
        while True:
            try:
                return self._connect(timeout)
            except Exception as e:
                if timeout is None:
                    raise
                if time.time() - start >= timeout:
                    raise e
                if not self._connect_exc_is_timeout(x):
                    raise
            time.sleep(delay)
            delay *= 1.41

    def _connect(self, timeout):
        raise NotImplementedError()

    def _connect_exc_is_timeout(self, e):
        raise NotImplementedError()

    def _should_put_close(self, con):
        pass

    def _get_nonidle_status(self, con):
        pass

    def put_connection(self, con, close=False, warn_status=True):

        if con.closed:
            return

        close = close or len(self.pool) >= self.max_idle

        if self._should_put_close(con):
            con.close()
            return

        nonidle = self._get_nonidle_status(con)
        if nonidle:
            if warn_status:
                log.warning("Connection from {0[0]}:{0[1]} returned with non-idle status {1}.".format(
                    con._origin,
                    nonidle,
                ))
            if not close:
                con.rollback()

        if close:
            con.close()
            return

        if con not in self.pool:
            self._checked_out.remove(con)
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

    def execute(self, query, params=None):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(query, params, 1)
        return self._build_context(con, cur)

    _paramstyle = None

    @classmethod
    def _quote_identifier(cls, name):
        # This is valid for sqlite3 and psycopg2.
        return '"{}"'.format(name.replace('"', '""'))

    _types = {}

    @classmethod
    def _adapt_type(cls, name):
        return cls._types.get(name.lower(), name)


class ConnectionContext(object):

    """Context manager for returning connections back to the pool.

    Note that this is not a proxy for the object; You need to use this
    as a context manager to get the object.

    """

    def __init__(self, engine, con, obj):
        self._engine = engine
        self._con = con
        self._obj = obj

    def __repr__(self):
        if self._con is self._obj:
            return '<ConnectionContext con={}>'.format(self._con)
        else:
            return '<ConnectionContext con={} obj={}>'.format(self._con, self.obj)

    def put_connection(self, *args, **kwargs):
        if self._con is not None:
            self._engine.put_connection(self._con, *args, **kwargs)
            self._con = None
    
    def __enter__(self):
        return self._obj

    def __exit__(self, *args):
        self.put_connection()




