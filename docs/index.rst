DB-API X
========

``dbapix`` is a unification of, and extension to, several DB-API 2.0 drivers.

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
- interaction with 3rd-party libraries, e.g. Pandas;
- automatic SSH tunnels.


Examples
--------


Create a connection pool, and "borrow" a connection from it (which will be
automatically returned when exiting the context)::

    from dbapix import create_engine

    # Create an engine with the name of the driver. Here we're connecting to
    # a PostgreSQL database via the `psycopg2` package.
    engine = create_engine('postgres',
        host='localhost',
        database='example',
    )

    # Context managers provide reliable resource management; the connection
    # will be returned to the pool when exiting this context.
    with engine.connect() as con:

        foo_id = 123

        # If not provided explicitly, parameters are pulled
        # from the calling scope for an f-string-like experience
        # but where Bobby Tables won't cause trouble.
        cur = con.cursor()
        cur.execute('''SELECT bar FROM foo WHERE id = {foo_id}''')

        for row in cur:
            # Values are accessible by index or name.
            print(row['bar'])

You can also manually manage connections, and directly turn results into
Pandas dataframes::

    from dbapix import create_engine

    # Lets use SQLite this time, via the `sqlite3` driver.
    engine = create_engine('sqlite', 'mydatabase.db')

    # Take ownership of a connection. This is now our responsibility to
    # either close, or return to the pool via `engine.put_connection(con)`.
    con = engine.get_connection()

    # Connections have an `execute` method which creates a cursor for us.
    cur = con.execute('''
        SELECT foo, sum(bar) AS bar
        FROM myawesometable
        GROUP BY baz
    ''')
    
    # Turn the result into a Pandas DataFrame!
    df = cur.as_dataframe()


If you need an SSH tunnel to connect, you can give a set of kwargs to be passed
to a `SSHTunnelForwarder <https://github.com/pahaz/sshtunnel>`_ for the Postgres
and MySQL engines::

    from dbapix import create_engine

    engine = create_engine('postgres',
        database='only_on_remote',
        tunnel=dict(
            host='database.example.com',
        ),
    )

    # The tunnel will be created at the first connection.

    engine.close() # Shut it down explicitly.


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
