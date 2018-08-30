
from . import *


class GenericTestMixin(object):

    def create_engine(self):
        raise NotImplementedError()

    def test_basics(self):

        db = self.create_engine()

        with db.connect() as con:

            con.execute('''DROP TABLE IF EXISTS test_basics''')
            con.execute('''CREATE TABLE test_basics (id {SERIAL!t} PRIMARY KEY, value INTEGER NOT NULL)''')
            con.execute('''INSERT INTO test_basics (value) VALUES ({})''', [123])
            cur = con.execute('''SELECT * FROM test_basics''')

            row = list(cur)[0]
            self.assertEqual(row, [1, 123])
            self.assertEqual(row['id'], 1)
            self.assertEqual(row['value'], 123)

            # TODO: Get DictCursor to work with next(cur) as well!

    def test_transactions(self):

        db = self.create_engine()

        con1 = db.get_connection()
        con2 = db.get_connection()

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

