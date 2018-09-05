import os

from unittest import TestCase

from dbapix import bind, create_engine


def get_environ_subset(prefix, lower=True):
    subset = {}
    for k, v in os.environ.items():
        if k.startswith(prefix):
            k = k[len(prefix):].strip('_')
            if lower:
                k = k.lower()
            subset[k] = v
    return subset

