
Engines
=======

.. currentmodule:: dbapix.engine

.. autoclass:: Engine

.. autoclass:: SocketEngine


Automatic Connection
--------------------

Connections are managed via a connection pool in the engine. These methods are the recommended way to access those connections, as they are context managers that will automatically return the connection to the pool.

All kwargs are passed to :meth:`Engine.get_connection`.

.. automethod:: Engine.connect

.. automethod:: Engine.cursor

.. automethod:: Engine.execute


Manual Connections
------------------

You can also manually checkout and return connections from the pool:

.. doctest::

    con = engine.get_connection()
    try:
        # Use the connection.
        cur = con.cursor()
        cur.execute('SELECT 1')
    finally:
        # Return it.
        engine.put_connection(con)

.. warning:: You must either return the connection via :meth:`Engine.put_connection`
    or close the connection via :meth:`.Connection.close` to avoid resource leaks (and
    deadlocks in some cases).

.. automethod:: Engine.get_connection

.. automethod:: Engine.put_connection


Helpers
-------

.. automethod:: Engine.quote_identifier

.. automethod:: Engine.adapt_type

