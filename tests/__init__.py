import functools
import os
import sys

from unittest import TestCase
from unittest.case import SkipTest

from dbapix import bind, get_engine_class, create_engine


def needs_imports(*modules):
    def decorator(func):
        @functools.wraps(func)
        def _needs_imports(*args, **kwargs):
            for mod in modules:
                try:
                    __import__(mod, fromlist=[''])
                except ImportError:
                    raise SkipTest('needs {}'.format(', '.join(modules)))
            return func(*args, **kwargs)
        return _needs_imports
    return decorator


def get_environ_subset(prefix, lower=True):
    subset = {}
    for k, v in os.environ.items():
        if k.startswith(prefix):
            k = k[len(prefix):].strip('_')
            if lower:
                k = k.lower()
            subset[k] = v
    return subset

