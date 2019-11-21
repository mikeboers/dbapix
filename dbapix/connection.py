import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Connection(object):
    
    """A normalized connection to a database.

    See `the DB-API 2.0 specs <https://www.python.org/dev/peps/pep-0249/#connection-objects>`_
    for the minimal methods provided there.

    """
    
    def __init__(self, engine, con):

        self._engine = engine

        self.wrapped = con

        # For tracking state around `begin()`.
        self._autocommit = None
    
    # The next 3 are here mostly for the docs.
    
    @property
    def closed(self):
        """Has this connection been closed?"""
        return self.wrapped.closed

    def fileno(self):
        return self.wrapped.fileno()

    def close(self):
        """Close the connection immediately.

        This prevents the engine from reusing connections, and so is discouraged
        unless you are sure the connection should not be reused.

        """
        self.wrapped.close()
    
    def reset_session(self, autocommit=False):
        """Reset the connection to an initial clean state.

        This is automatically called when connections are retreived from an engine,
        and is designed so that every connection feels like a new one, even
        though they are reused.

        """
        self.autocommit = autocommit

    def _should_put_close(self):
        pass

    def _get_nonidle_status(self):
        pass

    def __getattr__(self, key):
        """Attributes that are not provided by dbapix are passed through to the wrapped connection."""
        return getattr(self.wrapped, key)

    def cursor(self):
        """Get a :class:`.Cursor` for this connection.

        .. testcode::

            cur = con.cursor()
            cur.execute('SELECT 1')
            assert next(cur)[0] == 1

        """
        raw_cur = self.wrapped.cursor()
        return self._engine.cursor_class(self._engine, raw_cur)

    @abc.abstractmethod
    def _can_disable_autocommit(self):
        pass

    @property
    def autocommit(self):
        """Is every query executed in an implicit transaction that is auto committed?

        Defaults to ``True`` on new connections.
        """

        return self.wrapped.autocommit
    @autocommit.setter
    def autocommit(self, value):
        self.wrapped.autocommit = value

    def __enter__(self):

        # DB-API2 Connection.__enter__ doesn't actually do anything, and
        # replies on the implicit start of transactions.

        # Assert that we're not autocommitting.
        self._begin()

        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

    def begin(self):
        """Assert that we are or will be in a transaction.

        :return: A context manager that will automatically
            rollback or commit the current transaction.

        If it can be avoided, this does not actually start a transaction,
        but instead asserts that the connection is not in autocommit mode.
        If autocommit cannot be disabled, then an explicit ``BEGIN``
        will be executed.

        :meth:`commit` and :meth:`rollback` restore autocommit to
        it's value when :meth:`begin` was called.

        """
        self._begin()
        return TransactionContext(self)

    def _begin(self):

        # Optimize to use the included methods if we can. We will drop back
        # into autocommit mode later.
        if self.autocommit and self._can_disable_autocommit():
            self._autocommit = True
            self.autocommit = False

        # If we can't drop autocommit, then issue an explicit BEGIN.
        if self.autocommit:
            self.execute('BEGIN')

    def _end(self):
        if self._autocommit is not None:
            self.autocommit = self._autocommit
            self._autocommit = None

    def commit(self):
        """Commit changes made since the transaction started."""
        if self.autocommit:
            raise RuntimeError("Connection is in autocommit mode.")
        self.wrapped.commit()
        self._end()

    def rollback(self):
        """Rollback changes made since the transaction started."""
        if self.autocommit:
            raise RuntimeError("Connection is in autocommit mode.")
        self.wrapped.rollback()
        self._end()

    def execute(self, query, params=None):
        """Create a cursor, and execute a query on it in one step.

        :return: The created :class:`.Cursor`.

        .. seealso:: :meth:`.Cursor.execute` for parameters and examples.

        """
        # No cursor context here since it needs to be read.
        cur = self.cursor()
        cur.execute(query, params, 1)
        return cur

    def select(self, *args, **kwargs):
        """Pythonic wrapper for selecting.

        .. seealso:: :meth:`.Cursor.select` for parameters and examples.

        """
        kwargs['_stack_depth'] = 1
        # No cursor context here since it needs to be read.
        cur = self.cursor()
        return cur.select(*args, **kwargs)

    def insert(self, *args, **kwargs):
        """Pythonic wrapper for inserting.

        .. seealso:: :meth:`.Cursor.insert` for parameters and examples.

        """
        with self.cursor() as cur:
            return cur.insert(*args, **kwargs)

    def update(self, *args, **kwargs):
        """Pythonic wrapper for updating.

        .. seealso:: :meth:`.Cursor.update` for parameters and examples.

        """
        kwargs['_stack_depth'] = 1
        with self.cursor() as cur:
            return cur.update(*args, **kwargs)


class TransactionContext(object):

    def __init__(self, con):
        self._con = con

    def __enter__(self):
        return self._con

    def __exit__(self, exc_type=None, *args):
        if exc_type:
            self._con.rollback()
        else:
            self._con.commit()

    def __getattr__(self, key):
        return getattr(self._con, key)

