
from . import *


class TestQueryBuilding(TestCase):

    def test_basics(self):

        engine = create_engine('sqlite', ':memory:')
        con = engine.get_connection()

        con.execute('''CREATE TABLE foo (id INTEGER PRIMARY KEY, value INTEGER NOT NULL)''')

        con.insert('foo', dict(value=123))
        row = next(con.execute('''SELECT * FROM foo'''))
        self.assertEqual(tuple(row), (1, 123))

        con.update('foo', dict(value=234), 'id = {}', [1])
        row = next(con.execute('''SELECT * FROM foo'''))
        self.assertEqual(tuple(row), (1, 234))

        row = next(con.select('foo', '*'))
        self.assertEqual(tuple(row), (1, 234))

        row = next(con.select('foo', ['id', 'value']))
        self.assertEqual(tuple(row), (1, 234))

        con.insert('foo', dict(value=345))

        row = next(con.select('foo', ['value'], 'id = {}', [2]))
        self.assertEqual(tuple(row), (345, ))


    def test_update_from_stack(self):

        engine = create_engine('sqlite', ':memory:')
        con = engine.get_connection()

        con.execute('''CREATE TABLE foo (id INTEGER PRIMARY KEY, value INTEGER NOT NULL)''')

        con.insert('foo', dict(value=123))
        con.insert('foo', dict(value=234))

        id_ = 2
        con.update('foo', dict(value=345), where='id = {id_}')

        rows = list(con.select('foo', ['value']))
        self.assertEqual(rows, [(123, ), (345, )])
