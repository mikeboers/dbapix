from . import *


class TestCursor(TestCase):

    def create_engine(self):
        return create_engine('sqlite', 'sqlite-cursors.db')

    def test_cursor_chaining(self):

        db = self.create_engine()
        con = db.get_connection()
        cur = con.cursor()
        cur2 = cur.execute('''SELECT 1''')
        self.assertIs(cur, cur2)

    def test_fetches(self):

        db = self.create_engine()
        con = db.get_connection()
        cur = con.cursor()

        cur.execute('''CREATE TABLE IF NOT EXISTS test_fetches (id INTEGER PRIMARY KEY, value INTEGER)''')
        for i in range(1, 9):
            cur.insert('test_fetches', dict(value=i * 100))

        cur.execute('''SELECT * FROM test_fetches''')

        row = cur.fetchone()
        self.assertEqual(tuple(row), (1, 100))

        rows = cur.fetchmany(3)
        self.assertEqual([tuple(r) for r in rows], [(2, 200), (3, 300), (4, 400)])

        rows = cur.fetchall()
        self.assertEqual([tuple(r) for r in rows], [(5, 500), (6, 600), (7, 700), (8, 800)])

