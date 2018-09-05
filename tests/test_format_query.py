from . import *

from dbapix import bind
from dbapix.drivers.psycopg2 import Engine as Postgres
from dbapix.drivers.sqlite3 import Engine as SQLite


global_bar = 345

class TestFormatQuery(TestCase):

    def test_engines(self):

        # Identifiers.

        bq = bind('SELECT * FROM {table:table} WHERE id = {id}', dict(table='foo', id=123))
        q, p = bq()
        self.assertEqual(q, 'SELECT * FROM "foo" WHERE id = ?')
        self.assertEqual(p, [123])

        q, p = bq(SQLite)
        self.assertEqual(q, 'SELECT * FROM "foo" WHERE id = ?')
        self.assertEqual(p, [123])

        q, p = bq(Postgres)
        self.assertEqual(q, 'SELECT * FROM "foo" WHERE id = %s')
        self.assertEqual(p, [123])

        # Serial primary keys.

        bq = bind('CREATE TABLE foo (id {SERIAL PRIMARY KEY!t})')
        q, p = bq()
        self.assertEqual(q, 'CREATE TABLE foo (id SERIAL PRIMARY KEY)')
        self.assertEqual(p, [])

        q, p = bq(SQLite)
        self.assertEqual(q, 'CREATE TABLE foo (id INTEGER PRIMARY KEY)')
        self.assertEqual(p, [])

        # Gotta pass through the underlying ones.

        q, p = bind('SELECT %s', [1])()
        self.assertEqual(q, 'SELECT %s')
        self.assertEqual(p, [1])

        q, p = bind('SELECT ?', [1])()
        self.assertEqual(q, 'SELECT ?')
        self.assertEqual(p, [1])

    def test_escaped_params(self):

        foo = 123

        bound = bind('''SELECT '%s' ''')
        q, p = bound(Postgres)
        self.assertEqual(q, '''SELECT '%s' ''')
        
        bound = bind('''SELECT '%s', {foo} ''')
        q, p = bound(Postgres)
        self.assertEqual(q, '''SELECT '%%s', %s ''')

    def test_scope(self):

        foo = 234

        q, p = bind('SELECT {foo}, {global_bar}')()
        self.assertEqual(q, 'SELECT ?, ?')
        self.assertEqual(p, [234, 345])

        # Expressions.
        q, p = bind('SELECT {foo + global_bar}')()
        self.assertEqual(q, 'SELECT ?')
        self.assertEqual(p, [234 + 345])

        # Deep expressions.
        foodict=dict(foo=456)
        q, p = bind('SELECT {foodict["foo"]}')()
        self.assertEqual(q, 'SELECT ?')
        self.assertEqual(p, [456])
        
