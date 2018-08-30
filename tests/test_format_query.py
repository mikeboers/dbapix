from . import *

from dbapix.drivers.psycopg2 import Engine as Postgres
from dbapix.drivers.sqlite3 import Engine as SQLite


class TestFormatQuery(TestCase):

    def test_format_query(self):

        # Identifiers.

        q, p = Postgres.format_query('SELECT * FROM {table:table} WHERE id = {id}', dict(table='foo', id=123))
        self.assertEqual(q, 'SELECT * FROM "foo" WHERE id = %s')
        self.assertEqual(p, [123])

        q, p = SQLite.format_query('SELECT * FROM {table:table} WHERE id = {id}', dict(table='foo', id=123))
        self.assertEqual(q, 'SELECT * FROM "foo" WHERE id = ?')
        self.assertEqual(p, [123])


        # Serial primary keys.

        q, p = Postgres.format_query('CREATE TABLE foo (id {SERIAL PRIMARY KEY!t})')
        self.assertEqual(q, 'CREATE TABLE foo (id SERIAL PRIMARY KEY)')
        self.assertEqual(p, [])

        q, p = SQLite.format_query('CREATE TABLE foo (id {SERIAL PRIMARY KEY!t})')
        self.assertEqual(q, 'CREATE TABLE foo (id INTEGER PRIMARY KEY)')
        self.assertEqual(p, [])


        # Gotta pass through the underlying ones.

        q, p = Postgres.format_query('SELECT %s', [1])
        self.assertEqual(q, 'SELECT %s')
        self.assertEqual(p, [1])

        q, p = Postgres.format_query('SELECT ?', [1])
        self.assertEqual(q, 'SELECT ?')
        self.assertEqual(p, [1])

