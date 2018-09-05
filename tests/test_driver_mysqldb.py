import os

from . import *
from .test_driver_generic import GenericTestMixin


def create_mysql_engine():
    kwargs = get_environ_subset('DBAPIX_TEST_MYSQLDB')
    kwargs.setdefault('host', 'localhost')
    kwargs.setdefault('database', 'dbapix')
    return create_engine('mysqldb', kwargs)


class TestMySQLDBGenerics(GenericTestMixin, TestCase):

    def _create_engine(self):
        return create_mysql_engine()

