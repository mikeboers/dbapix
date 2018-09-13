
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
