import os

from . import *
from .test_driver_generic import GenericTestMixin


def create_mysql_engine():
    return create_engine('pymysql', dict(
        host=    os.environ.get('DBAPIX_TEST_PYMYSQL_HOST'    , 'su01.mm'),
        database=os.environ.get('DBAPIX_TEST_PYMYSQL_DATABASE', 'sandbox'),
        password=os.environ.get('DBAPIX_TEST_PYMYSQL_PASSWORD', 'xxx'),
    ))


class TestPyMySQLGenerics(GenericTestMixin, TestCase):

    def _create_engine(self):
        return create_mysql_engine()


class TestPyMySQL(TestCase):

    pass
