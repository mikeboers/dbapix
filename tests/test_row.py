import collections

import six

from . import *


class TestRow(TestCase):

    def test_both_apis(self):

        db = create_engine('sqlite3', ':memory:')
        con = db.get_connection()

        con.execute('''CREATE TABLE foo (id INTEGER PRIMARY KEY, value INTEGER NOT NULL)''')
        con.insert('foo', dict(id=1, value=123))

        row = con.execute('''SELECT * FROM foo''').fetchone()

        self.assertIsInstance(row, tuple)
        # self.assertIsInstance(row, collections.Mapping)

        self.assertEqual(repr(row), '<Row id=1, value=123>')
        self.assertEqual(str(row),  '<Row id=1, value=123>')

        self.assertEqual(len(row), 2)

        self.assertEqual(row, (1, 123))
        # self.assertEqual(row, dict(id=1, value=123))

        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], 123)
        self.assertRaises(IndexError, lambda: row[2])
        self.assertIn(0, row)
        self.assertIn(1, row)
        self.assertNotIn(2, row)

        self.assertEqual(row['id'], 1)
        self.assertEqual(row['value'], 123)
        self.assertRaises(KeyError, lambda: row['notakey'])
        self.assertIn('id', row)
        self.assertIn('value', row)
        self.assertNotIn('notakey', row)
        self.assertEqual(row.get('id'), 1)
        self.assertEqual(row.get('notakey', 'bar'), 'bar')
        self.assertIs(row.get('notakey'), None)

        self.assertEqual(list(row), [1, 123])

        self.assertEqual(list(row.keys()), ['id', 'value'])
        self.assertEqual(list(row.values()), [1, 123])
        self.assertEqual(list(row.items()), [('id', 1), ('value', 123)])

        self.assertEqual(row.copy(), dict(id=1, value=123))

        if six.PY2:

            self.assertIsInstance(row.iterkeys(), collections.Iterator)
            self.assertIsInstance(row.itervalues(), collections.Iterator)
            self.assertIsInstance(row.iteritems(), collections.Iterator)

            self.assertEqual(list(row.iterkeys()), ['id', 'value'])
            self.assertEqual(list(row.itervalues()), [1, 123])
            self.assertEqual(list(row.iteritems()), [('id', 1), ('value', 123)])

            self.assertIsInstance(row.keys(), list)
            self.assertIsInstance(row.values(), list)
            self.assertIsInstance(row.items(), list)

        else:

            self.assertIsInstance(row.keys(), collections.Iterator)
            self.assertIsInstance(row.values(), collections.Iterator)
            self.assertIsInstance(row.items(), collections.Iterator)
