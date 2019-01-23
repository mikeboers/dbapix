import os

from dbapix.registry import Registry

from . import *
from .test_driver_generic import GenericTestMixin



class TestRegistry(TestCase):

    def test_basics(self):

        registry = Registry()
        registry.register('foo', 'sqlite', os.path.abspath(os.path.join(__file__, '..', 'sqlite.db')))

        engine = registry.create_engine('foo')
        con = engine.get_connection()
        cur = con.execute('select 1 as foo')

