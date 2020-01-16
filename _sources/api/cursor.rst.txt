
Cursors
=======

.. currentmodule:: dbapix.cursor

.. autoclass:: Cursor


Executing
---------

.. automethod:: Cursor.execute


Fetching Results
----------------

Direct
~~~~~~

You can call a variety of methods to get your data back as :class:`.Row` objects:

.. automethod:: Cursor.fetchone

.. automethod:: Cursor.fetchmany

.. automethod:: Cursor.fetchall

Iteration
~~~~~~~~~

You can also treat the cursor as an iterator, e.g.:

.. testcode::

    for row in cur.execute('SELECT * FROM foo'):
        # Do something with the row.
        pass


Pandas DataFrame
~~~~~~~~~~~~~~~~

.. automethod:: Cursor.as_dataframe


Query Builders
--------------

.. automethod:: Cursor.select

.. automethod:: Cursor.insert

.. automethod:: Cursor.update



Wrapped
-------

.. attribute:: Cursor.wrapped

    This is the underlying DB-API2 cursor object, in case you need to access it.

.. automethod:: Cursor.__getattr__






