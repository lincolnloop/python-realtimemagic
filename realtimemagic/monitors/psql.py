import functools

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from eventlet.hubs import trampoline

class PsqlMonitor(object):
    def __init__(self, dsn):
        self.dsn = dsn

    def monitor(self, channel):
        def wrapper(f):
            @functools.wraps(f)
            def inner(pubsub):
                cnn = psycopg2.connect(self.dsn)
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
        cur.execute("NOTIFY %s, '%s';" % (channel, message))
        cur.close()
        cnn.close()
