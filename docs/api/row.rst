
Rows
====

.. currentmodule:: dbapix.row

.. autoclass:: Row

.. automethod:: Row.__getitem__


Dict-like
---------


.. automethod:: Row.get

.. automethod:: Row.copy

The next 3 have the appropriate behaviour in Python 2 or Python 3

.. automethod:: Row.keys
.. automethod:: Row.values
.. automethod:: Row.items

The following are also defined as in Python 2:

.. automethod:: Row.iterkeys
.. automethod:: Row.viewkeys
.. automethod:: Row.itervalues
.. automethod:: Row.viewvalues
.. automethod:: Row.iteritems
.. automethod:: Row.viewitems


Row Lists
---------

.. autoclass:: RowList

.. automethod:: RowList.as_dataframe
