
Connections
===========

.. currentmodule:: dbapix.connection

.. autoclass:: Connection


Cursors and Convenience
-----------------------

.. automethod:: Connection.cursor

.. automethod:: Connection.execute

.. automethod:: Connection.select

.. automethod:: Connection.insert

.. automethod:: Connection.update


Transactions
------------

Transaction management is one of the larger normalization efforts of dbapix.

Connections start in "autocommit" mode (and can be inspected by :attr:`Connection.autocommit`).
When in autocommit, the connection behaves as if it automatically commits after every query; your changes are immediately reflected in the database and availible to other connections.

When not in autocommit, the connection ensures it is in a transaction before
executing a query, and the user must call :meth:`Connection.commit` for changes
to be reflected in the database (or may call :meth:`Connection.rollback` to rollback).

Regardless of the state of autocommit, you can enter a transaction by using
the connection as a context manager, or calling :meth:`Connection.begin`. Autocommit
is restored after the transaction if it was set before.

You can use a connection as a context manager to implicitly
:meth:`~Connection.begin`/:meth:`~Connection.commit`/:meth:`~Connection.rollback`::

    with con:
        # Do stuff.
        pass

or you can call the methods explicitly::

    con.begin()
    try:
        # Do stuff.
        pass
    except:
        con.rollback()
    else:
        con.commit()


.. autoattribute:: Connection.autocommit

.. automethod:: Connection.begin

.. automethod:: Connection.commit

.. automethod:: Connection.rollback


Session
-------

.. autoattribute:: Connection.closed

.. automethod:: Connection.close

.. automethod:: Connection.reset_session

.. automethod:: Connection.fileno


Wrapped
-------

.. attribute:: Connection.wrapped

    This is the underlying DB-API2 connection object, in case you need to access it.

.. automethod:: Connection.__getattr__






