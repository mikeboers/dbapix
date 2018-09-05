import os

from dbapix.drivers.psycopg2 import Engine

from . import *
from .test_driver_generic import GenericTestMixin


def create_pg_engine():
    return create_engine('psycopg2', dict(
        host=    os.environ.get('DBAPIX_TEST_PSYCOPG2_HOST'    , 'su01.mm'),
        database=os.environ.get('DBAPIX_TEST_PSYCOPG2_DATABASE', 'sandbox'),
    ))


class TestPsycopg2Generics(GenericTestMixin, TestCase):

    def _create_engine(self):
        return create_pg_engine()


class TestPsycopg2(TestCase):

    def test_generic_names(self):
        self.assertIs(get_engine_class('postgres'), Engine)
        self.assertIs(get_engine_class('postgresql'), Engine)
