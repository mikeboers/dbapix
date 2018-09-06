import os

from dbapix.drivers.psycopg2 import Engine

from . import *
from .test_driver_generic import GenericTestMixin


@needs_imports('psycopg2')
def create_pg_engine():
    kwargs = get_environ_subset('DBAPIX_TEST_PSYCOPG2')
    kwargs.setdefault('host', 'localhost')
    kwargs.setdefault('database', 'dbapix')
    return create_engine('psycopg2', kwargs)


class TestPsycopg2Generics(GenericTestMixin, TestCase):

    def _create_engine(self):
        return create_pg_engine()


class TestPsycopg2(TestCase):

    def test_generic_names(self):
        self.assertIs(get_engine_class('postgres'), Engine)
        self.assertIs(get_engine_class('postgresql'), Engine)
