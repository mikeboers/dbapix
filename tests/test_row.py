import collections

import six

from . import *


class TestRow(TestCase):

    def test_both_apis(self):

        db = create_engine('sqlite3', ':memory:')
        con = db.get_connection()

        con.execute('''CREATE TABLE thetable (id INTEGER PRIMARY KEY, value STRING NOT NULL)''')
        con.insert('thetable', dict(id=1, value='foo'))

        row = con.execute('''SELECT * FROM thetable''').fetchone()

        self.assertIsInstance(row, tuple)
        # self.assertIsInstance(row, collections.Mapping)

        if six.PY2:
            repr_ = "<Row id=1, value=u'foo'>"
        else:
            repr_ = "<Row id=1, value='foo'>"
        self.assertEqual(repr(row), repr_)
        self.assertEqual(str(row),  repr_)

        self.assertEqual(len(row), 2)

        self.assertEqual(row, (1, 'foo'))
        # self.assertEqual(row, dict(id=1, value='foo'))

        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], 'foo')
        self.assertRaises(IndexError, lambda: row[2])
        self.assertIn(1, row)
        self.assertIn('foo', row)
        self.assertNotIn('notavalue', row)

        self.assertEqual(row['id'], 1)
        self.assertEqual(row['value'], 'foo')
        self.assertRaises(KeyError, lambda: row['notakey'])
        self.assertIn('id', row)
        self.assertIn('value', row)
        self.assertNotIn('notakey', row)
        self.assertEqual(row.get('id'), 1)
        self.assertEqual(row.get('notakey', 'bar'), 'bar')
        self.assertIs(row.get('notakey'), None)

        self.assertIn('value', row.viewkeys())
        self.assertNotIn('value', row.viewvalues())
        self.assertNotIn('foo', row.viewkeys())
        self.assertIn('foo', row.viewvalues())

        self.assertEqual(list(row), [1, 'foo'])

        self.assertEqual(list(row.keys()), ['id', 'value'])
        self.assertEqual(list(row.values()), [1, 'foo'])
        self.assertEqual(list(row.items()), [('id', 1), ('value', 'foo')])

        self.assertEqual(row.copy(), dict(id=1, value='foo'))

        if six.PY2:

            self.assertIsInstance(row.iterkeys(), collections.KeysView)
            self.assertIsInstance(row.itervalues(), collections.ValuesView)
            self.assertIsInstance(row.iteritems(), collections.ItemsView)

            self.assertEqual(list(row.iterkeys()), ['id', 'value'])
            self.assertEqual(list(row.itervalues()), [1, 'foo'])
            self.assertEqual(list(row.iteritems()), [('id', 1), ('value', 'foo')])

            self.assertIsInstance(row.keys(), list)
            self.assertIsInstance(row.values(), list)
            self.assertIsInstance(row.items(), list)

        else:

            self.assertIsInstance(row.keys(), collections.KeysView)
            self.assertIsInstance(row.values(), collections.ValuesView)
            self.assertIsInstance(row.items(), collections.ItemsView)
