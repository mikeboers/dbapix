import logging
import sys
import time
import weakref
import re
import abc
import itertools

import six

from .query import bind as bind_query
from .connection import Connection
from .cursor import Cursor
from .row import Row


_engine_counter = itertools.count(0)


@six.add_metaclass(abc.ABCMeta)
class Engine(object):

    connection_class = Connection
    cursor_class = Cursor
    row_class = Row

    paramstyle = abc.abstractproperty(None)
    placeholder = abc.abstractproperty(None)

    def __init__(self):
        self.pool = []
        self.max_idle = 2
        self._checked_out = []
        self._context_refs = {}
        self._engine_counter = next(_engine_counter)
        self._log = logging.getLogger('{}[{}]'.format(__name__, self._engine_counter))

    def close(self):
        for collection in (self.pool, self._checked_out):
            while collection:
                collection.pop().close()

    def __del__(self):
        self.close()

    def get_connection(self, timeout=None, **kwargs):
        
        try:
            while True:
                con = self.pool.pop(0)
                # This actually happens in FarmSoup.
                if not con.closed:
                    break
                self._log.warning("Connection fileno {1} last from {0[0]}:{0[1]} was closed.".format(
                    con._origin,
                    con._fileno,
                ))
        except IndexError:
            real_con = self._new_connection(timeout)
            con = self.connection_class(self, real_con)
            con._fileno = con.fileno() # Postgres closses it.

        stack_depth = 1 + kwargs.pop('_stack_depth', 0)

        self._checked_out.append(con)
        con._reset_session(**kwargs)

        # Store where it came from so we can warn later.
        frame = sys._getframe(stack_depth)
        con._origin = (frame.f_code.co_filename, frame.f_lineno)

        return con

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

    @abc.abstractmethod
    def _connect(self, timeout):
        pass

    @abc.abstractmethod
    def _connect_exc_is_timeout(self, e):
        pass

    def put_connection(self, con, close=False, warn_status=True):

        if con.closed:
            return

        close = close or len(self.pool) >= self.max_idle

        if con._should_put_close():
            con.close()
            return

        nonidle = con._get_nonidle_status()
        if nonidle:
            if warn_status:
                self._log.warning("Connection from {0[0]}:{0[1]} returned with non-idle status {1}.".format(
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
        kwargs['_stack_depth'] = 1 + kwargs.get('_stack_depth', 0)
        con = self.get_connection(*args, **kwargs)
        return self._build_context(con, con)

    def cursor(self, *args, **kwargs):
        kwargs['_stack_depth'] = 1 + kwargs.get('_stack_depth', 0)
        con = self.get_connection(*args, **kwargs)
        cur = con.cursor()
        return self._build_context(con, cur)

    def execute(self, query, params=None):
        con = self.get_connection(_stack_depth=1)
        cur = con.cursor()
        cur.execute(query, params, 1)
        return self._build_context(con, cur)

    @classmethod
    def _quote_identifier(cls, name):
        # This is valid for sqlite3 and psycopg2.
        return '"{}"'.format(name.replace('"', '""'))

    _types = {}

    @classmethod
    def _adapt_type(cls, name):
        return cls._types.get(name.lower(), name)


class SocketEngine(Engine):

    def __init__(self, connect_kwargs=None, tunnel=None, **kwargs):
        super(SocketEngine, self).__init__()

        if (connect_kwargs and kwargs) or not (connect_kwargs or kwargs):
            raise ValueError("Please provide one of connect_kwargs or **kwargs.")

        self.connect_kwargs = connect_kwargs or kwargs

        if isinstance(tunnel, dict):
            self.tunnel_kwargs = tunnel
            self.tunnel = None
        else:
            self.tunnel_kwargs = None
            self.tunnel = tunnel

    def close(self):
        super(SocketEngine, self).close()
        if self.tunnel:
            self.tunnel.close()
            self.tunnel = None

    def _new_connection(self, *args):

        # We're overriding _new_connection instead of making an explicit
        # `_prep_tunnel` or something. Maybe do that later?

        if self.tunnel_kwargs and not self.tunnel:

            if 'ssh_address_or_host' not in self.tunnel_kwargs:
                address = self.tunnel_kwargs.pop('ssh_address', None)
                host = self.tunnel_kwargs.pop('host', None)
                port = self.tunnel_kwargs.pop('port', 22)
                if (host and address) or not (host or address):
                    raise ValueError("Provide one of ssh_address_or_host, ssh_address, or host.")
                if address and port:
                    raise ValueError("Provide one of ssh_address_or_host/ssh_address or host/port.")
                self.tunnel_kwargs['ssh_address_or_host'] = address or (host, port)

            if 'remote_bind_address' not in self.tunnel_kwargs:
                host = self.tunnel_kwargs.pop('remote_bind_host', '127.0.0.1')
                port = self.connect_kwargs.pop('port', self.default_port)
                self.tunnel_kwargs['remote_bind_address'] = (host, port)


            from sshtunnel import SSHTunnelForwarder
            self.tunnel = SSHTunnelForwarder(**self.tunnel_kwargs)
            self.tunnel.start()

        if self.tunnel:
            self.connect_kwargs['host'] = '127.0.0.1'
            self.connect_kwargs['port'] = self.tunnel.local_bind_port

        return super(SocketEngine, self)._new_connection(*args)


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
            return '<ConnectionContext con={} obj={}>'.format(self._con, self._obj)

    def put_connection(self, *args, **kwargs):
        if self._con is not None:
            self._engine.put_connection(self._con, *args, **kwargs)
            self._con = None
    
    def __enter__(self):
        return self._obj

    def __exit__(self, *args):
        self.put_connection()




