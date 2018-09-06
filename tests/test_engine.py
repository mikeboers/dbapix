from . import *

from dbapix.drivers.sqlite3 import Engine as SQLiteEngine
from dbapix import get_engine_class

 
class TestEngine(TestCase):


    def test_get_engine_class(self):

        cls = get_engine_class('sqlite')
        self.assertIs(cls, SQLiteEngine)

        cls = get_engine_class('sqlite3')
        self.assertIs(cls, SQLiteEngine)

        self.assertRaises(ImportError, get_engine_class, 'notadriver')
