import os

from . import *
from .test_generic import GenericTestMixin


def create_pg_engine():
    return create_engine('psycopg2', dict(
        host=    os.environ.get('DBAPIX_TEST_PSYCOPG2_HOST'    , 'su01'),
        database=os.environ.get('DBAPIX_TEST_PSYCOPG2_DATABASE', 'sandbox'),
    ))


class TestPsycopg2Generics(GenericTestMixin, TestCase):

    def create_engine(self):
        return create_pg_engine()

