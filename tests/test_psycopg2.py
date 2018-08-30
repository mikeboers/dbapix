import os

from . import *
from .test_generic import GenericTestMixin


class TestPsycopg2Generics(GenericTestMixin, TestCase):

    SERIAL = 'SERIAL'
    
    def create_engine(self):
        return create_engine('psycopg2', dict(
            host=    os.environ.get('DBAPIX_TEST_PSYCOPG2_HOST'    , 'su01'),
            database=os.environ.get('DBAPIX_TEST_PSYCOPG2_DATABASE', 'sandbox'),
        ))


