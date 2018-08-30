from collections import Mapping, Sequence
import logging
import sys
import time
import weakref

try:
    import _string
    basestring = str
except ImportError:
    # We're only using two special methods here.
    _string = str


log = logging.getLogger()


class Engine(object):

    def __init__(self):
        self.pool = []
        self.max_idle = 2
        self._context_refs = {}

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

        return con

    def _prepare_connection(self, con, **kwargs):
        pass

    def _new_connection(self, timeout):
        start = time.time()
        delay = 0.1
        while True:
            try:
                return self._connect()
            except Exception as e:
                if timeout is None:
                    raise
                if time.time() - start >= timeout:
                    raise e
                if not self._connect_exc_is_timeout(x):
                    raise
            time.sleep(delay)
            delay *= 1.41

    def _connect(self):
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
        status = con.get_transaction_status()

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

    _paramstyle = None

    @classmethod
    def _quote_identifier(cls, name):
        # TODO: DO BETTER!
        return '"{}"'.format(name)

    _types = {}

    @classmethod
    def _get_type(cls, name):
        return cls._types.get(name.lower(), name)

    @classmethod
    def format_query(cls, query, params=()):

        is_named = isinstance(params, Mapping)
        if not is_named and (isinstance(params, basestring) or not isinstance(params, Sequence)):
            raise ValueError("Params must be mapping or non-str sequence.")

        out_params = []
        out_parts = []

        if cls._paramstyle == '?':
            next_param = lambda: '?'
        elif cls._paramstyle == 'format':
            next_param = lambda: '%s'
        else:
            raise NotImplementedError(cls._paramstyle)

        next_first_index = 0

        for literal, field_name, format_spec, conversion in _string._formatter_parser(query):

            if literal:
                out_parts.append(literal)
            if field_name is None:
                continue

            # {SERIAL!t} is looked up directly.
            if not conversion:
                pass
            elif conversion in ('t', ):
                out_parts.append(cls._get_type(field_name))
                continue
            else:
                raise ValueError("Unsupported convertion {!r}.".format(convertion))

            first, rest = _string._formatter_field_name_split(field_name)

            if not first:
                first = next_first_index
            
            if not first or isinstance(first, int):
                next_first_index = first + 1

            value = params[first]
            for is_attr, x in rest:
                if is_attr:
                    value = getattr(value, x)
                else:
                    value = value[x]

            if not format_spec:
                pass

            elif format_spec.lower() in ('i', 'ident', 'identifier', 'table', 'column'):
                out_parts.append(cls._quote_identifier(value))
                continue

            elif format_spec.lower() in ('t', 'type'):
                out_parts.append(cls._get_type(value))
                continue

            else:
                raise ValueError("Unsupported format spec {!r}".format(format_spec))

            out_parts.append(next_param())
            out_params.append(value)

        if not is_named:
            out_params.extend(params[next_first_index:])
        return ''.join(out_parts), out_params


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




