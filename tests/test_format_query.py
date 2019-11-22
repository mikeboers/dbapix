from . import *

from dbapix import bind
from dbapix.drivers.psycopg2 import Engine as Postgres
from dbapix.drivers.sqlite3 import Engine as SQLite
from dbapix.drivers.ctds import Engine as CTDS


global_bar = 345

class TestFormatQuery(TestCase):

    def test_engines(self):

        # Identifiers.

        bq = bind('SELECT * FROM {table:i} WHERE id = {id}', dict(table='foo', id=123))
        q, p = bq()
        self.assertEqual(q, 'SELECT * FROM "foo" WHERE id = ?')
        self.assertEqual(p, [123])

        q, p = bq(SQLite)
        self.assertEqual(q, 'SELECT * FROM "foo" WHERE id = ?')
        self.assertEqual(p, [123])

        q, p = bq(Postgres)
        self.assertEqual(q, 'SELECT * FROM "foo" WHERE id = %s')
        self.assertEqual(p, [123])

        q, p = bq(CTDS)
        self.assertEqual(q, 'SELECT * FROM [foo] WHERE id = :0')
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

    def test_indexes(self):

        q, p = bind('SELECT {0}, {1}', ('foo', 'bar'))()
        self.assertEqual(q, 'SELECT ?, ?')
        self.assertEqual(p, ['foo', 'bar'])

        q, p = bind('SELECT {1}, {0}', ('foo', 'bar'))()
        self.assertEqual(q, 'SELECT ?, ?')
        self.assertEqual(p, ['bar', 'foo'])

        q, p = bind('SELECT {0}, {1}, {0}', ('foo', 'bar'))()
        self.assertEqual(q, 'SELECT ?, ?, ?')
        self.assertEqual(p, ['foo', 'bar', 'foo'])


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
    
    def test_values(self):

        bound = bind('INSERT INTO foo VALUES {x:values}', dict(x=(1, 123)))

        q, p = bound()
        self.assertEqual(q, 'INSERT INTO foo VALUES (?, ?)')
        self.assertEqual(p, [1, 123])

        q, p = bound(Postgres)
        self.assertEqual(q, 'INSERT INTO foo VALUES (%s, %s)')

    def test_multi_values(self):

        bound = bind('INSERT INTO foo VALUES {x:values_list}', dict(x=[
            (1, 123),
            (2, 234),
        ]))

        q, p = bound()
        self.assertEqual(q, 'INSERT INTO foo VALUES (?, ?), (?, ?)')
        self.assertEqual(p, [1, 123, 2, 234])

    def test_literal(self):

        func = 'now'
        bound = bind('SELECT {func:literal}()')
        q, p = bound()
        self.assertEqual(q, 'SELECT now()')

    def test_partial_provided(self):
        self.assertRaises(KeyError, bind, 'SELECT {foo}, {bar}', dict(foo=123))

        