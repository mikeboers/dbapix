from collections import Mapping, Sequence
import logging
import sys
import time
import weakref
import re

try:
    import _string
    str_formatter_parser = _string.formatter_parser
    str_formatter_field_name_split = _string.formatter_field_name_split
    basestring = str

except ImportError:
    # We're only using two special methods here.
    str_formatter_parser = str._formatter_parser
    str_formatter_field_name_split = str._formatter_field_name_split

log = logging.getLogger()


py_identifier_re = re.compile(r'^[_a-zA-Z]\w*$')


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

    def execute(self, *args, **kwargs):
        con = self.get_connection()
        cur = con.cursor()
        cur.execute(*args, **kwargs)
        return self._build_context(con, cur)

    _paramstyle = None

    @classmethod
    def _quote_identifier(cls, name):
        # This is valid for sqlite3 and psycopg2.
        return '"{}"'.format(name.replace('"', '""'))

    _types = {}

    @classmethod
    def _get_type(cls, name):
        return cls._types.get(name.lower(), name)

    @classmethod
    def format_query(cls, query, params=None, _frame_depth=1):

        is_magic = params is None
        is_named = isinstance(params, Mapping)
        is_indexed = not (is_magic or is_named)
        if is_indexed and (isinstance(params, basestring) or not isinstance(params, Sequence)):
            raise ValueError("Params must be None, mapping, or non-str sequence.")

        out_params = []
        out_parts = []

        if cls._paramstyle == 'qmark':
            next_param = lambda: '?'
        elif cls._paramstyle == 'format':
            next_param = lambda: '%s'
        else:
            raise NotImplementedError(cls._paramstyle)

        next_index = 0

        for literal_prefix, field_spec, format_spec, conversion in str_formatter_parser(query):

            if literal_prefix:
                out_parts.append(literal_prefix)
            if field_spec is None:
                continue

            # {SERIAL!t} and {name!i} are taken directly.
            # This might not be a great idea...
            if not conversion:
                pass
            elif conversion in ('i', ):
                out_parts.append(cls._quote_identifier(field_spec))
                continue
            elif conversion in ('t', ):
                out_parts.append(cls._get_type(field_spec))
                continue
            else:
                raise ValueError("Unsupported convertion {!r}.".format(convertion))

            if field_spec:
                is_index = field_spec.isdigit()
                is_simple = is_index or py_identifier_re.match(field_spec)
                if is_index:
                    field_spec = int(field_spec)
            else:
                field_spec = next_index
                is_index = is_simple = True

            if is_index:
                next_index = field_spec + 1
                if not is_indexed:
                    raise ValueError("Cannot use indexes to lookup into non-indexed params.")

            if params is None:
                # Lets finally load the "magic".
                frame = sys._getframe(_frame_depth)
                params = dict(frame.f_globals)
                params.update(frame.f_locals)

            if is_simple:
                # Bypass the magic as much as possible.
                value = params[field_spec]
            else:
                #print(is_index, is_simple, repr(field_spec))
                value = eval(field_spec, params, {})

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

        if is_indexed:
            out_params.extend(params[next_index:])
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




