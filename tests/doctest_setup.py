import os
import random
import datetime

import dbapix


try:
    root = os.path.abspath(os.path.join(__file__, '..', '..'))
except NameError:
    root = os.path.abspath('..')


sandbox = os.path.abspath(os.path.join(
    root,
    'sandbox',
    str(datetime.datetime.now().date()),
    str(random.randrange(1e6)),
))
os.makedirs(sandbox)


db_path = os.path.join(sandbox, 'sqlite.db')

engine = dbapix.create_engine('sqlite', db_path)


con = engine.get_connection()


con.execute('CREATE TABLE foo (value INTEGER, bar INTEGER, baz INTEGER)')
con.insert('foo', dict(value=123))

con.execute('CREATE TABLE bar (foo INTEGER, value INTEGER, baz INTEGER)')
con.insert('bar', dict(foo=123))


cur = con.cursor()
