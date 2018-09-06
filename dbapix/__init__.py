from .query import bind


generic_implementations = dict(
    mariadb=['mysqldb', 'pymysql'],
    mysql=['mysqldb', 'pymysql'],
    postgres=['psycopg2'],
    postgresql=['psycopg2'],
    sqlite=['sqlite3'],
)


def get_engine_class(driver):

    driver = driver.lower()

    specifics = generic_implementations.get(driver)
    if specifics:
        for real_driver in specifics:
            try:
                return get_engine_class(real_driver)
            except ImportError:
                pass
        raise ValueError("None of {} availible for {!r}.".format(specifics, driver))

    # TODO: Be able to be smarter about why drivers are missing; is the driver
    # actually not supported, or is it missing dependencies?
    mod_name = 'dbapix.drivers.{}'.format(driver)
    mod = __import__(mod_name, fromlist=[''])
    return getattr(mod, 'Engine')


def create_engine(driver, *args, **kwargs):
    """Build an :class:`.Engine` for the given driver::

        engine = create_engine('postgres',
            host='localhost',
            database='example',
        )

    :param str driver: The name of the database driver to use

    The name can be either a specific implementation (e.g. ``"psycopg2"``), or
    it can be generic. Generic names will be resolved to the first availible
    specific implementation (e.g. ``"mysql"`` resolves to the first of
    ``"mysqldb"`` or ``"pymysql"`` to exist.)

    All ``args`` and ``kwargs`` are passed to the engine constructor.

    """
    
    cls = get_engine_class(driver)
    return cls(*args, **kwargs)

