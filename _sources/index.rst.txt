dbapix
======

**dbapix** is a unification of, and extension to, several DB-API 2.0 drivers.

We currently wrap:

- ``"postgres"`` via `psycopg2 <http://initd.org/psycopg/>`_
- ``"sqlite"`` via `sqlite3 <https://docs.python.org/3.7/library/sqlite3.html>`_
- ``"mysql"`` via `PyMySQL <https://github.com/PyMySQL/PyMySQL>`_ or `MySQL-Python <https://pypi.org/project/MySQL-python/>`_

The first goal is to provide a :class:`pool <.Engine>` of normalized
DB-API 2.0 :class:`connections <.Connection>` and :class:`cursors <.Cursor>`,
and for them to have the same Python API and semantics regardless of the driver.

The second goal is to provide some common niceties:

- f-string-like parameter binding;
- high-level functions, e.g. ``insert``, ``update``, etc.;
- dict-like rows;
- interaction with 3rd-party libraries, e.g. Pandas.


Example
-------

::

    from dbapix import create_engine

    # Create an engine with the name of the driver.
    engine = create_engine('postgres', dict(
        host='localhost',
        database='example',
    ))

    # Context managers provide reliable resource management.
    with engine.connect() as con:

        foo_id = 123

        # If not provided explicitly, parameters are pulled
        # from the calling scope for an f-string-like experience
        # but where Bobby Tables won't cause trouble.
        cur = con.execute('''SELECT bar FROM foo WHERE id = {foo_id}''')

        for row in cur:
            # Values are accessible by index or name.
            print(row['bar'])



API Reference
-------------
.. toctree::

   api/core
   api/engine
   api/connection
   api/cursor
   api/row
   api/query

---

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
