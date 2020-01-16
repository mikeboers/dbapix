

.. _params:

Parameters
==========

dbapix has gone to a great effort to normalize parameter binding, and especially in emulating "magic" f-string syntax that pulls values from the execution scope.

There are currently 3 general styles of parameter binding that are automatically picked from based on their appearance in a query, and the passing of explicit params:

-
    If there are usable curly brace pairs, and no params, :ref:`fstring_style` is used.

    .. testcode::
        
        foo = 123
        cur.execute('SELECT {foo}')
        assert next(cur)[0] == 123

-  
    If there are usable curly brace pairs, and params, :ref:`format_style` is used.

    .. testcode::

        # Named:
        cur.execute('SELECT {foo}', dict(foo=456))
        assert next(cur)[0] == 456

        # Positional params:
        cur.execute('SELECT {}', (123, ))
        assert next(cur)[0] == 123

-
    Otherwise, the :ref:`wrapped_style` is used.
    
    .. testcode::

        cur.execute('SELECT ?', (123, ))
        assert next(cur)[0] == 123


.. _format_style:

Format Style
------------

This style mimics the ``str.format`` method, as described by `Format String Syntax <https://docs.python.org/3/library/string.html#format-string-syntax>`_ in the Python docs.

It is not identical, however. The practical differences are:

- For non-integer fields, the expression is evaluated directly (like f-strings). The incompatibility is that string keys need to be quoted, e.g. ``field['key']`` instead of ``field[key]``.
- The conversions via ``!`` no longer work.
- The format spec language has been replaced, and is much simpler:

.. list-table::
    :header-rows: 1
    :widths: 25, 75

    * - Spec
      - Meaning

    * - ``i``, ``ident``, or ``identifier``
      - The value should be quoted as an identifier by :meth:`.Engine.quote_identifier`.

    * - ``t``, or ``type``
      - The value should be converted to the engine's syntax by :meth:`.Engine.adapt_type`.

    * - ``l``, or ``literal``
      - The value should be inserted as-is, without any quoting.

    * - ``v``, or ``values``
      - The value should be formatted as a ``VALUES`` tuple.

    * - ``vl``, or ``values_list``
      - The value should be formatted as a list of ``VALUES`` tuples.

Field examples:

.. testcode::

    # Implicit position:
    cur.execute('''SELECT {}, {}''', (1, 2))
    assert next(cur) == (1, 2)

    # Explicit position:
    cur.execute('''SELECT {1}, {0}''', (1, 2))
    assert next(cur) == (2, 1)

    # Named:
    cur.execute('''SELECT {foo}''', dict(foo=123))
    assert next(cur)[0] == 123

    # Sub fields:
    cur.execute('''SELECT {foo[0]}, {bar['baz']}''', dict(foo=(1, 2, 3), bar=dict(baz=4)))
    assert next(cur) == (1, 4)

    # Expressions:
    cur.execute('''SELECT {foo + bar}''', dict(foo=1, bar=2))
    assert next(cur)[0] == 3


Format spec examples:

.. testcode::

    # Identifiers:
    cur.execute('''SELECT * FROM {:i}''', ['foo'])
    assert next(cur)[0] == 123

    # Types:
    cur.execute('''CREATE TABLE type_example (id {'SERIAL PRIMARY KEY':type}, value INTEGER)''')

    # Literals:
    cur.execute('''SELECT {:literal}''', ['''date('now')'''])

    # Values:
    cur.execute('''INSERT INTO bar VALUES {:values}''', [(1, 2, 3)])

    # Values list:
    cur.execute('''INSERT INTO bar VALUES {:values_list}''', [[(1, 2, 3), (4, 5, 6)]])





.. _fstring_style:

F-String Style
--------------

This style is an extension of the :ref:`format_style` and mimics the ``f'{foo}'`` style described by `Formatted string literals <https://docs.python.org/3/reference/lexical_analysis.html#f-strings>`_ in the Python docs; it evalutes the expressions in the namespace that `execute` (or similar) was called:

.. testcode::

    foo = 123
    cur.execute('''SELECT {foo}''')  # NOTE no params passed here!
    assert next(cur)[0] == 123

Note that unlike Python f-strings, this is only able to pull values from the calling scope and it's global scope. It is not able to bind to values in other enclosing scopes::

    foo = 1

    def outer():

        # This is not visible as a parameter.
        bar = 2

        def inner():

            baz = 3

            # This will fail due to `bar`.
            cur.execute('''SELECT {foo}, {bar}, {baz}''')

        inner()


.. warning:: You **must** not use the ``f`` prefix on the strings. These are not actually f-strings, but merely mimic them. If you accidentally use f-strings directly you will expose your code to SQL injection vulnerabilities.


.. _wrapped_style:

Wrapped Style
-------------

This is the style employed by the wrapped database, and depends on the ``Cursor.paramstyle`` attribute.

In the case of SQLite, this is ``'?'``:

.. testcode::

    cur.execute('SELECT ?', (123, ))
    assert next(cur)[0] == 123

If you want to use curly braces in a wrapped-style query, they must be escaped by doubling:

.. testcode::

    cur.execute('SELECT "{{0}}", ?', (123, ))
    assert next(cur) == ('{0}', 123)
