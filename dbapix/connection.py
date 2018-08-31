

class ConnectionMixin(object):
    
    def __init__(self, *args, **kwargs):
        super(ConnectionMixin, self).__init__(*args, **kwargs)
        self._autocommit = None
    
    def cursor(self, *args, **kwargs):
        cur = super(ConnectionMixin, self).cursor(*args, **kwargs)
        cur._engine = self._engine
        return cur

    def _can_disable_autocommit(self):
        return True

    def begin(self):
        
        # Optimize to use the included methods if we can. We will drop back
        # into autocommit mode later.
        if self.autocommit and self._can_disable_autocommit():
            self._autocommit = True
            self.autocommit = False

        if self.autocommit:
            self.cursor().execute('BEGIN')

        # DB-API2 Connection.__enter__ doesn't actually do anything.
        # We rely upon implicit start of transactions.

        return TransactionContext(self)

    def _end(self):
        if self._autocommit is not None:
            self.autocommit = self._autocommit
            self._autocommit = None

    def commit(self):
        if self.autocommit:
            raise RuntimeError("Connection is in autocommit mode.")
        super(ConnectionMixin, self).commit()
        self._end()

    def rollback(self):
        if self.autocommit:
            raise RuntimeError("Connection is in autocommit mode.")
        super(ConnectionMixin, self).rollback()
        self._end()

    def execute(self, *args, **kwargs):
        # No cursor context here since it needs to be read.
        cur = self.cursor()
        cur.execute(*args, **kwargs)
        return cur

    def select(self, *args, **kwargs):
        # No cursor context here since it needs to be read.
        cur = self.cursor()
        return cur.select(*args, **kwargs)

    def insert(self, *args, **kwargs):
        with self.cursor() as cur:
            return cur.insert(*args, **kwargs)

    def update(self, *args, **kwargs):
        with self.cursor() as cur:
            return cur.update(*args, **kwargs)


class TransactionContext(object):

    def __init__(self, con):
        self._con = con

    def __enter__(self):
        # Both sqlite3 and psycopg2 don't actually do anything on __enter__
        # except return themselves.
        return self._con.__enter__()

    def __exit__(self, exc_type=None, *args):
        if exc_type:
            self._con.rollback()
        else:
            self._con.commit()

    def __getattr__(self, key):
        return getattr(self._con, key)

