import os

from . import *
from .test_generic import GenericTestMixin


def create_sqlite_engine():
    return create_engine('sqlite3', os.path.abspath(os.path.join(__file__, '..', 'sqlite.db')))


class TestSQLite3Generics(GenericTestMixin, TestCase):

    def create_engine(self):
        return create_sqlite_engine()

