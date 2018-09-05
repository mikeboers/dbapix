import re
from collections import Mapping, Sequence
import sys


try:
    import _string
    str_formatter_parser = _string.formatter_parser
    basestring = str

except ImportError:
    # We're only using two special methods here.
    str_formatter_parser = str._formatter_parser


py_identifier_re = re.compile(r'^[_a-zA-Z]\w*$')


class Placeholder(str):

    def __sql__(self, engine):
        if engine:
            if engine._paramstyle == 'qmark':
                return '?'
            elif engine._paramstyle == 'format':
                return '%s'
            else:
                raise ValueError("Unknown paramstyle {!r}.".format(engine._paramstyle))
        return self


class Type(str):

    def __sql__(self, engine):
        if engine:
            return engine._adapt_type(self)
        return self


class Identifier(str):

    def __sql__(self, engine):
        if engine:
            return engine._quote_identifier(self)
        return '"{}"'.format(self.replace('"', '""'))


default_placeholder = Placeholder('?')


def bind(query, params=None, _stack_depth=0):
    bound = BoundQuery()
    bound.parse(query, params, _stack_depth + 1)
    return bound


class BoundQuery(object):

    def __init__(self, query=None, params=None, _stack_depth=0):
        self.query_parts = None
        self.params = None
        if query:
            self.parse(query, params, _stack_depth + 1)

    def __str__(self, engine=None):

        out = []

        escape_placeholders = None
        if engine and any(isinstance(x, Placeholder) for x in self.query_parts):
            if engine._paramstyle == 'format':
                escape_placeholders = lambda x: x.replace('%', '%%')

        for x in self.query_parts:
            sql_func = getattr(x, '__sql__', None)
            if sql_func:
                out.append(sql_func(engine))
            else:
                x = str(x)
                if escape_placeholders:
                    x = escape_placeholders(x)
                out.append(x)
        return ''.join(out)

    def __call__(self, engine=None):
        return self.__str__(engine), self.params

    def parse(self, query, params=None, _stack_depth=0):

        is_magic = params is None
        is_named = isinstance(params, Mapping)
        is_indexed = not (is_magic or is_named)
        if is_indexed and (isinstance(params, basestring) or not isinstance(params, Sequence)):
            raise ValueError("Params must be None, mapping, or non-str sequence.")

        self.params = out_params = []
        self.query_parts = out_parts = []

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
                out_parts.append(Indentifer(field_spec))
                continue
            elif conversion in ('t', ):
                out_parts.append(Type(field_spec))
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
                frame = sys._getframe(_stack_depth + 1)
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
                out_parts.append(Identifier(value))
                continue

            elif format_spec.lower() in ('t', 'type'):
                out_parts.append(Type(value))
                continue

            else:
                raise ValueError("Unsupported format spec {!r}".format(format_spec))

            out_parts.append(default_placeholder)
            out_params.append(value)

        if is_indexed:
            out_params.extend(params[next_index:])
