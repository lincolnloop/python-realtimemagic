import functools

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, adapt
from eventlet.hubs import trampoline


class PsqlMonitor(object):
    def __init__(self, dsn=None, database=None, user=None,
            password=None, host=None, port=None):
        self.dsn = dsn
        self.database = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port

    def monitor(self, channel):
        def wrapper(f):
            @functools.wraps(f)
            def inner(pubsub):
                cnn = psycopg2.connect(self.dsn, self.database, self.user,
                        self.password, self.host, self.port)
                cnn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                cur = cnn.cursor()
                cur.execute("LISTEN %s;" % channel)
                while 1:
                    trampoline(cnn, read=True)
                    cnn.poll()
                    while cnn.notifies:
                        n = cnn.notifies.pop()
                        f(n, pubsub)
            return inner
        return wrapper

    def notify(self, channel, message):
        cnn = psycopg2.connect(self.dsn)
        cnn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = cnn.cursor()
        cur.execute("NOTIFY %s, %s;" % (channel, adapt(message)))
        cur.close()
        cnn.close()
