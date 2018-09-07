
from . import *


class GenericTestMixin(object):

    def setUp(self):
        self.engines = []

    def tearDown(self):
        for db in self.engines:
            db.close()

    def create_engine(self):
        db = self._create_engine()
        self.engines.append(db)
        return db

    def _create_engine(self):
        raise NotImplementedError()

    def test_basics(self):

        db = self.create_engine()

        with db.connect() as con:

            con.execute('''DROP TABLE IF EXISTS test_basics''')
            con.execute('''CREATE TABLE test_basics (id {SERIAL PRIMARY KEY!t}, value INTEGER NOT NULL)''')
            con.execute('''INSERT INTO test_basics (value) VALUES ({})''', [123])

            cur = con.execute('''SELECT * FROM test_basics''')
            row = list(cur)[0]

            # The tuple/list-ness is not consistent between drivers so far.
            print('row type', type(row))
            print('row is tuple', isinstance(row, tuple))
            print('row is list', isinstance(row, list))

            self.assertEqual(tuple(row), (1, 123))
            self.assertEqual(row['id'], 1)
            self.assertEqual(row['value'], 123)

            self.assertIn('id', row)
            self.assertNotIn('foo', row)

            self.assertEqual(row.copy(), dict(id=1, value=123))

            # Make sure keys exist via `next` as well, since that doesn't
            # with psycopg2's DictCursor.
            cur = con.execute('''SELECT * FROM test_basics''')
            row = next(cur)
            self.assertEqual(tuple(row), (1, 123))
            self.assertEqual(row['id'], 1)

    def test_closed(self):
        db = self.create_engine()
        con = db.get_connection()
        self.assertFalse(con.closed)
        con.close()
        self.assertTrue(con.closed)

    def test_auto_binding(self):

        db = self.create_engine()
        with db.connect() as con:

            table = 'test_auto_binding'
            foo = 123
            bar = 234

            con.execute('''DROP TABLE IF EXISTS {table:i}''')
            con.execute('''CREATE TABLE {table:i} (id {SERIAL PRIMARY KEY!t}, value INTEGER NOT NULL)''')

            con.execute('''INSERT INTO {table:i}(value) VALUES ({foo})''')
            row = next(con.execute('''SELECT value FROM {table:i}'''))
            self.assertEqual(row[0], foo)


    def test_transactions(self):

        db = self.create_engine()

        # con2 must not start transactions because MySQL appears to have a
        # stricter isolation level than Postgres and SQLite do by default,
        # and after the first select it will not return other data.
        con1 = db.get_connection()
        con2 = db.get_connection(autocommit=True)

        self.assertFalse(con1.autocommit)
        self.assertTrue(con2.autocommit)
        
        with con1:
            con1.execute('''DROP TABLE IF EXISTS test_generic_transactions''')
            con1.execute('''CREATE TABLE test_generic_transactions (id {SERIAL!t} PRIMARY KEY, value INTEGER NOT NULL)''')

        def assert_count(count):
            rows = list(con2.select('test_generic_transactions', '*'))
            self.assertEqual(len(rows), count)


        # Implicit transactions.
        con1.insert('test_generic_transactions', dict(value=123))
        assert_count(0)

        con1.commit()
        assert_count(1)

        # Explicit transactions.
        with con1:
            con1.insert('test_generic_transactions', dict(value=234))
        assert_count(2)

        # Autocommit implicitly commits.
        con1.autocommit = True
        con1.insert('test_generic_transactions', dict(value=345))
        assert_count(3)

        # Autocommit doesn't stop explicit ones.
        with con1.begin():
            con1.insert('test_generic_transactions', dict(value=456))
            assert_count(3)
        assert_count(4)

        # Back to autocommit.
        con1.insert('test_generic_transactions', dict(value=567))
        assert_count(5)

        # Back to implicit.
        con1.autocommit = False
        con1.insert('test_generic_transactions', dict(value=678))
        assert_count(5)
        con1.commit()
        assert_count(6)

        # Implicit rollbacks.
        con1.insert('test_generic_transactions', dict(value=789))
        assert_count(6)
        con1.rollback()
        assert_count(6)

        # Explicit rollbacks.
        with con1.begin():
            con1.insert('test_generic_transactions', dict(value=789))
            assert_count(6)
            con1.rollback()
        assert_count(6)


