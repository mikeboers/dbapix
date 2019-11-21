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

from .params import Params


class SQL(str):
    """Placeholder for literal SQL.

    WARNING: This currently only works for Psycopg2.

    """
    pass


py_identifier_re = re.compile(r'^[_a-zA-Z]\w*$')


class Literal(str):

    def __sql__(self, engine):
        return self


class Placeholder(str):

    def __sql__(self, engine):
        if engine:
            return engine.placeholder
        return self

default_placeholder = Placeholder('?')


class Type(str):

    def __sql__(self, engine):
        if engine:
            return engine.adapt_type(self)
        return self


class Identifier(str):

    def __sql__(self, engine):
        if engine:
            return engine.quote_identifier(self)
        return '"{}"'.format(self.replace('"', '""'))


class Values(int):

    def __sql__(self, engine):
        placeholder = engine.placeholder if engine else '?'
        return '({})'.format(', '.join((placeholder, ) * self))


class MultiValues(object):

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def __sql__(self, engine):
        placeholder = engine.placeholder if engine else '?'
        row = '({})'.format(', '.join((placeholder, ) * self.cols))
        return ', '.join((row, ) * self.rows)




def bind(query, params=None, _stack_depth=0):
    return BoundQuery(query, params, _stack_depth + 1)


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
            if engine.paramstyle == 'format':
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

        # We defer doing the stack magic until we need it.
        if params is not None and not isinstance(params, Params):
            params = Params(params)

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
                next_index = max(next_index, field_spec + 1)

            # It is finally time to look up the stack.
            if params is None:
                params = Params.from_stack(_stack_depth + 1)

            if is_simple:
                # Bypass the magic as much as possible.
                value = params[field_spec]
            else:
                value = eval(compile(field_spec, '<{}>'.format(field_spec), 'eval'), params, {})

            if not format_spec:
                pass

            elif format_spec.lower() in ('i', 'ident', 'identifier'):
                out_parts.append(Identifier(value))
                continue

            elif format_spec.lower() in ('t', 'type'):
                out_parts.append(Type(value))
                continue

            elif format_spec.lower() in ('l', 'literal'):
                out_parts.append(Literal(value))
                continue

            elif format_spec.lower() in ('v', 'values'):
                value = tuple(value)
                out_parts.append(Values(len(value)))
                out_params.extend(value)
                continue

            elif format_spec.lower() in ('vl', 'values_list'):
                values = [tuple(x) for x in value]
                if len(set(map(len, values))) != 1:
                    raise ValueError("Elements of multi_values are not the same size.")
                out_parts.append(MultiValues(len(values), len(values[0])))
                for x in values:
                    out_params.extend(x)
                continue

            else:
                raise ValueError("Unsupported format spec {!r}".format(format_spec))

            out_parts.append(default_placeholder)
            out_params.append(value)

        # If there is anything positional left, absorb it.
        if params is not None:
            out_params.extend(params[next_index:])
