

class ConnectionMixin(object):
    
    def begin(self):
        return TransactionContext(self)

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
        # All supported drivers don't actually do anything on __enter__.
        return self._con

    def __exit__(self, exc_type=None, *args):
        if exc_type:
            self._con.rollback()
        else:
            self._con.commit()

    def __getattr__(self, key):
        return getattr(self._con, key)

