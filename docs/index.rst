dbapix
======

**dbapix** is a unification of, and extension to, several DB-API 2.0 drivers.

We currently wrap:

- ``psycopg2`` `(docs) <http://initd.org/psycopg/>`_
- ``sqlite3`` `(docs) <https://docs.python.org/3.7/library/sqlite3.html>`_
- ``pymysql`` `(GitHub) <https://github.com/PyMySQL/PyMySQL>`_


Example
-------

::

    from dbapix import create_engine

    # Create an engine with the name of the driver.
    engine = create_engine('psycopg2', dict(
        host='localhost',
        database='example',
    ))

    # Context managers provide reliable resource management.
    with engine.connect() as con:

        foo_id = 123

        # If not provided explicitly, parameters are pulled
        # from the calling scope for an f-string-like experience
        # where Bobby Tables won't cause trouble.
        cur = con.execute('''SELECT bar FROM foo WHERE id = {foo_id}''')

        for row in cur:
            # Values are accessible by index or name.
            print(row['bar'])



Table of Contents
-----------------
.. toctree::

   index

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


API Reference
-------------

Core
~~~~

.. autofunction:: dbapix.create_engine


Engines
~~~~~~~

.. currentmodule:: dbapix.engine

.. autoclass:: Engine


Manual Connection Management
............................

Connections are managed via a connection pool in the engine. You can manually
checkout and return connections; you must either return or close connections
that you checkout to avoid resource leaks (and deadlocks in some cases).

.. automethod:: Engine.get_connection

.. automethod:: Engine.put_connection


Automatic Connection Management
...............................

.. automethod:: Engine.connect

.. automethod:: Engine.cursor

.. automethod:: Engine.execute


Connections
~~~~~~~~~~~

.. currentmodule:: dbapix.connection

.. autoclass:: Connection


Cursors
~~~~~~~

.. currentmodule:: dbapix.cursor

.. autoclass:: Cursor

.. automethod:: Cursor.execute

.. automethod:: Cursor.fetchone

.. automethod:: Cursor.as_dataframe


Rows
~~~~

.. currentmodule:: dbapix.row

.. autoclass:: Row


Queries
~~~~~~~

.. currentmodule:: dbapix.query

.. autofunction:: bind

.. autoclass:: BoundQuery


