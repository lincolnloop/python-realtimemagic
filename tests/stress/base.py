# -*- coding: utf-8 -*-
"""
    sockjs-tornado benchmarking server. Works as a simple chat server
    without HTML frontend and listens on port 8080 by default.
"""
import sys

from tornado import web, ioloop

from sockjs.tornado import SockJSRouter, SockJSConnection


class EchoConnection(SockJSConnection):
    """Echo connection implementation"""
    clients = set()

    def on_open(self, info):
        # When new client comes in, will add it to the clients list
        self.clients.add(self)

    def slow_stuff(self, num):
        print 'Executing a slow query...'
        import psycopg2
        cnn = psycopg2.connect(dsn='dbname=snarl')
        cur = cnn.cursor()
        cur.execute("SELECT pg_sleep(%s);" % num)
        cur.close()
        cnn.close()

    def on_message(self, msg):
        # For every incoming message, broadcast it to all clients
        # self.slow_stuff(5) # This does not handle out of loop requests!
        self.broadcast(self.clients, msg)

    def on_close(self):
        # If client disconnects, remove him from the clients list
        self.clients.remove(self)

    @classmethod
    def dump_stats(cls):
        # Print current client count
        print 'Clients: %d' % (len(cls.clients))

if __name__ == '__main__':
    options = dict()

    if len(sys.argv) > 1:
        options['immediate_flush'] = False

    # 1. Create SockJSRouter
    EchoRouter = SockJSRouter(EchoConnection, '/pubsub', options)

    # 2. Create Tornado web.Application
    app = web.Application(EchoRouter.urls)

    # 3. Make application listen on port 8080
    app.listen(9000)

    # 4. Every 1 second dump current client count
    ioloop.PeriodicCallback(EchoConnection.dump_stats, 1000).start()

    # 5. Start IOLoop
    ioloop.IOLoop.instance().start()
