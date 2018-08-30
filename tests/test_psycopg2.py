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


class TestPsycopg2(TestCase):

    def test_format_query(self):

        db = create_pg_engine()

        q, p = db.format_query('SELECT * FROM {table:table} WHERE id = {id}', dict(table='foo', id=123))
        self.assertEqual(q, 'SELECT * FROM "foo" WHERE id = %s')
        self.assertEqual(p, [123])

        q, p = db.format_query('CREATE TABLE foo (id {SERIAL!t} PRIMARY KEY)')
        self.assertEqual(q, 'CREATE TABLE foo (id SERIAL PRIMARY KEY)')
        self.assertEqual(p, [])
