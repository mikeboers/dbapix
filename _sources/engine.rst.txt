
Engines
=======

.. currentmodule:: dbapix.engine

.. autoclass:: Engine


Manual Connections
------------------

Connections are managed via a connection pool in the engine. You can manually
checkout and return connections; you must either return or close connections
that you checkout to avoid resource leaks (and deadlocks in some cases).

.. automethod:: Engine.get_connection

.. automethod:: Engine.put_connection


Automatic Connection
--------------------

.. automethod:: Engine.connect

.. automethod:: Engine.cursor

.. automethod:: Engine.execute

