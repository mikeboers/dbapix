import os

from dbapix.drivers.psycopg2 import Engine

from . import *
from .test_driver_generic import GenericTestMixin


@needs_imports('psycopg2')
@needs_imports('sshtunnel')
def create_tunnel_engine():
    kwargs = get_environ_subset('DBAPIX_TEST_TUNNEL_CON')
    tunnel = get_environ_subset('DBAPIX_TEST_TUNNEL_SSH')
    kwargs.setdefault('host', 'localhost')
    kwargs.setdefault('database', 'dbapix')
    return create_engine('psycopg2', kwargs, tunnel)


class TestTunnelGenerics(GenericTestMixin, TestCase):

    def _create_engine(self):
        return create_tunnel_engine()

