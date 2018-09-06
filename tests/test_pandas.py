from . import *


class TestPandas(TestCase):

    def test_basics(self):

        db = create_engine('sqlite3', ':memory:')
        con = db.get_connection()

        con.execute('''CREATE TABLE foo (id INTEGER PRIMARY KEY, x INTEGER NOT NULL, y INTEGER NOT NULL)''')
        for x in range(10):
            con.insert('foo', dict(x=x, y=x**2))

        cur = con.execute('''SELECT * FROM foo''')
        df = cur.as_dataframe()

        self.assertEqual(list(df.columns), ['id', 'x', 'y'])
        self.assertEqual(df.shape, (10, 3))

        # We get an empty one at this point.
        df = cur.as_dataframe()
        self.assertEqual(df.shape, (0, 3))

        # We can manually pick the data we want to turn into a dataframe.
        cur.execute('''SELECT * FROM foo''')
        rows = cur.fetchall()
        df = cur.as_dataframe(rows[:5])
        self.assertEqual(df.shape, (5, 3))

        # We can use one of the columns as the index.
        df = con.execute('''SELECT * FROM foo''').as_dataframe(index='id')
        self.assertEqual(list(df.columns), ['x', 'y'])
        self.assertEqual(df.shape, (10, 2))
