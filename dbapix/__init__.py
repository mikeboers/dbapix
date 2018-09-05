from .query import bind


def get_engine_class(driver):
    mod = __import__('dbapix.drivers.{}'.format(driver), fromlist=[''])
    return getattr(mod, 'Engine')


def create_engine(driver, *args, **kwargs):
    """Build an :class:`.Engine` for the given driver.

    :param str driver: The name of the database driver to use.

    All other ``*args`` and ``**kwargs`` are passed to the engine constructor.

    """
    
    cls = get_engine_class(driver)
    return cls(*args, **kwargs)

