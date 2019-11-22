import os

from . import *
from .test_driver_generic import GenericTestMixin


@needs_imports('ctds')
def create_mysql_engine():
    kwargs = get_environ_subset('DBAPIX_TEST_CTDS')
    kwargs.setdefault('server', 'localhost')
    kwargs.setdefault('database', 'dbapix')
    return create_engine('ctds', kwargs)


class TestCTDSGenerics(GenericTestMixin, TestCase):

    def _create_engine(self):
        return create_mysql_engine()

