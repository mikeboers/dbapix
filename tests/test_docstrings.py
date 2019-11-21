from unittest import TestCase
import doctest
import pkgutil
import re
import os

import dbapix


setup_path = os.path.abspath(os.path.join(__file__, '..', 'doctest_setup.py'))
setup_source = open(setup_path).read()
setup_code = compile(setup_source, setup_path, 'exec')

def fix_doctests(suite):
    for case in suite._tests:

        # Add some more flags.
        case._dt_optionflags = (
            (case._dt_optionflags or 0) |
            doctest.IGNORE_EXCEPTION_DETAIL |
            doctest.ELLIPSIS |
            doctest.NORMALIZE_WHITESPACE
        )

        exec(setup_code, case._dt_test.globs)
        # case._dt_test.globs['dbapix'] = dbapix
        # case._dt_test.globs['engine'] = engine = dbapix.create_engine('sqlite', ':memory:')



def register_doctests(mod):

    if isinstance(mod, str):
        try:
            mod = __import__(mod, fromlist=[''])
        except ImportError:
            return

    try:
        suite = doctest.DocTestSuite(mod)
    except ValueError:
        return

    fix_doctests(suite)

    cls_name = 'Test' + ''.join(x.title() for x in mod.__name__.split('.'))
    cls = type(cls_name, (TestCase, ), {})

    for test in suite._tests:
        def func(self):
            return test.runTest()
        name = str('test_' + re.sub('[^a-zA-Z0-9]+', '_', test.id()).strip('_'))
        func.__name__ = name
        setattr(cls, name, func)

    globals()[cls_name] = cls


for importer, mod_name, ispkg in pkgutil.walk_packages(
    path=dbapix.__path__,
    prefix=dbapix.__name__ + '.',
    onerror=lambda x: None
):
    register_doctests(mod_name)

