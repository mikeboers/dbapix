from .query import bind


generic_implementations = dict(
    sqlite=['sqlite3'],
    postgres=['psycopg2'],
    postgresql=['psycopg2'],
    mysql=['mysqldb', 'pymysql'],
    mariadb=['mysqldb', 'pymysql'],
)


def get_engine_class(driver):

    driver = driver.lower()
    
    if driver in generic_implementations:
        for real_driver in generic_implementations[driver]:
            try:
                return get_engine_class(real_driver)
            except ImportError:
                pass
        raise ValueError("No drivers availible for {}.".format(driver))

    mod = __import__('dbapix.drivers.{}'.format(driver), fromlist=[''])
    return getattr(mod, 'Engine')


def create_engine(driver, *args, **kwargs):
    """Build an :class:`.Engine` for the given driver.

    :param str driver: The name of the database driver to use.

    All other ``*args`` and ``**kwargs`` are passed to the engine constructor.

    """
    
    cls = get_engine_class(driver)
    return cls(*args, **kwargs)

