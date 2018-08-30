from __future__ import absolute_import

import sqlite3

from dbapix.connection import ConnectionMixin as _ConnectionMixin
from dbapix.cursor import CursorMixin as _CursorMixin
from dbapix.engine import Engine as _Engine


class Engine(_Engine):

    _paramstyle = 'qmark'
    _types = {'serial primary key': 'INTEGER PRIMARY KEY'}
