

def get_engine_class(driver):
    mod = __import__('dbapix.drivers.{}'.format(driver), fromlist=[''])
    return getattr(mod, 'Engine')


def create_engine(driver, *args, **kwargs):
    cls = get_engine_class(driver)
    return cls(*args, **kwargs)

