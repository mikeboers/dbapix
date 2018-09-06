import os

from . import *
from .test_driver_generic import GenericTestMixin


@needs_imports('pymysql')
def create_mysql_engine():
    kwargs = get_environ_subset('DBAPIX_TEST_PYMYSQL')
    kwargs.setdefault('host', 'localhost')
    kwargs.setdefault('database', 'dbapix')
    return create_engine('pymysql', kwargs)


class TestPyMySQLGenerics(GenericTestMixin, TestCase):

    def _create_engine(self):
        return create_mysql_engine()


class TestPyMySQL(TestCase):

    pass
