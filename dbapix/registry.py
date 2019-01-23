
from . import create_engine as _create_engine


class Registry(object):

    """A simple store for multiple engine parameters.
    
    Used to abstract the connection/tunnel parameters from where they are used. E.g.::

        dbs = Registry()
        dbs.register('production', 'mysql',
            host='db.example.com',
            user='myuser',
            password='mypassword',
            database='mydatabase',
        )

        engine = dbs.create_engine('production')

    """

    def __init__(self):
        self.specs = {}

    def register(self, name, *args, **kwargs):
        """Register engine parameters under a name for later use.

        :param str name: The name to store the params under.
        :param args: Passed to :func:`.create_engine` by :meth:`create_engine`.
        :param kwargs: Passed to :func:`.create_engine` by :meth:`create_engine`.

        """
        self.specs[name] = (args, kwargs)

    def create_engine(self, name):
        """Create the named engine.

        :param str name: A name previous registered with :meth:`register`.
        :return: A freshly constructed :class:`.Engine`.

        """
        try:
            args, kwargs = self.specs[name]
        except KeyError:
            raise ValueError("No engine specs for {!r} in registry.".format(name))
        return _create_engine(*args, **kwargs)


