import sys
import threading
import logging
import json

from collections import defaultdict

from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection

import tornado.options
tornado.options.parse_command_line()

from auth import AuthenticationError
from concurrency import ThreadPool


class PubSubConnection(SockJSConnection):
    VALID_COMMANDS = ['subscribe', 'unsubscribe', 'publish', 'set_debug_session']

    def __init__(self, *args, **kwargs):
        super(PubSubConnection, self).__init__(*args, **kwargs)
        self.master = self.session.server.settings.get('master')
        self.cookies = None

    def set_debug_session(self, payload):
        if self.master.local:
            self.cookies = dict([payload.split('=', 1)])

    def publish(self, payload):
        logging.info('Publishing %s' % payload)
        self.authorize(payload['channel'])
        # We need to be able to hook things here.
        cont = True
        for trap in self.master.push_traps:
            cont = cont and trap(self, payload['channel'], payload['message'])
        if cont:
            self.master.publish(payload['channel'], payload['message'], async=False)

    def authorize(self, channel):
        #This will probably block the thread. Consider add_handler.
        try:
            for authenticator in self.master.authenticators.get(channel, []):
                authenticator.check(self, channel)
            else:
                for authenticator in self.master.authenticators.get('default', []):
                    authenticator.check(self, channel)
        except AuthenticationError, e:
            self.send({'controlMessage': True, 'content': e})
            logging.info(e)  # send control message
            self.close()
        except Exception, e:
            logging.error(e)

    def subscribe(self, payload):
        channel = payload['channel']
        self.authorize(channel)
        subscriptions = self.master.subscriptions
        if channel not in subscriptions or self not in subscriptions[channel]:
            subscriptions[channel].append(self)
            logging.info('Subscribing %s to %s' % (self, channel))  # send control message
        self.send({'controlMessage': True, 'content': 'Subscribed to %s' % channel})

    def unsubscribe(self, payload):
        channel = payload['channel']
        subscriptions = self.master.subscriptions
        logging.info('Unsubscribing %s from channel %s' % (self, channel))  # send control message
        if self in subscriptions[channel]:
            subscriptions[channel].remove(self)
        self.send({'controlMessage': True, 'content': 'Unsubscribed from %s' % channel})

    def handle_receivers(self, message):
        # This could be improved by moving the loop into the thread instead of
        # each receiver
        # logging.info('Handling through receivers')
        for receiver in self.master.receivers:
            if self.master.async:
                self.master.workers.add_task(receiver, self, message)
            else:
                receiver(self, message)

    def on_message(self, message):  # Needs Refactor
        logging.info('Received message %s' % message)
        obj = None
        try:
            obj = json.loads(message)
        except ValueError, e:
            pass  # logging.error(e)

        if not obj or not isinstance(obj, dict):
            self.handle_receivers(message)
            return

        try:
            command, payload = obj.get('action', None), obj.get('payload', None)
            if command and command in self.VALID_COMMANDS:
                if self.master.async:
                    self.master.workers.add_task(getattr(self, command), payload)
                else:
                    getattr(self, command)(payload)
            else:
                self.handle_receivers(message)
        except Exception, e:
            logging.error(e)

    def on_open(self, conn_info):
        for opening in self.master.openings:
            if self.master.async:
                self.master.workers.add_task(opening, self, conn_info)
            else:
                opening(self, conn_info)

    def on_close(self):
        logging.info('Unsubscribing %s' % self)
        subscriptions = self.master.subscriptions
        for channel in subscriptions.keys():
            if self in subscriptions[channel]:
                subscriptions[channel].remove(self)


def chunks(l, n):
    "Splits a list into <n-sized lists"
    return [l[i:i + n] for i in range(0, len(l), n)]


class RealTimeMagic(object):
    monitors = []

    def __init__(self, *args, **kwargs):
        # Use a better datastructure for subscriptions
        # Consider a self-locking dict
        self.subscriptions = defaultdict(list)  # consider spawning threads
        # Authenticators can be a normal dict
        self.authenticators = defaultdict(list)
        # Functions to handle an incomming message
        self.openings = []
        self.receivers = []
        self.push_traps = []
        self.closings = []

        self.ioloop = ioloop.IOLoop.instance()

        self.local = kwargs.get('local', False)
        self.async = kwargs.get('async', True)
        if self.async:
            self.workers = ThreadPool(kwargs.get('threads', 64))

    def start(self):
        self.router = SockJSRouter(PubSubConnection, '/pubsub',
            user_settings={'master': self})

        app = web.Application(self.router.urls)
        app.listen(9000)
        for monitor in self.monitors:
            t = threading.Thread(target=monitor, args=(self,))
            t.daemon = True
            t.start()

        t = threading.Thread(target=self.ioloop.start)
        t.daemon = True
        t.start()
        logging.info('Realtime listener started.')

        # Returning control to the parent application so we can catch keyword
        # interrupts.
        try:
            while 1:
                t.join(1)
                if not t.isAlive():
                    break
        except KeyboardInterrupt:
            print '\nExiting...'
            sys.exit(1)

    def slow_stuff(self, num):
        print 'Executing a slow query...'
        import psycopg2
        cnn = psycopg2.connect(dsn='dbname=snarl')
        cur = cnn.cursor()
        cur.execute("SELECT pg_sleep(%s);" % num)
        cur.close()
        cnn.close()

    def _publish(self, connections, message):
        #self.slow_stuff(10)
        logging.info('Broadcasting message...')
        self.router.broadcast(connections, message)
        #for ws in connections:
        #    ws.send(message)

    def publish(self, channel, message, async=True):
        """
        This is already being handled asynchronously when comming from the
        connection.
        """
        if self.async and async:
            self.workers.add_task(getattr(self, '_publish'), self.subscriptions[str(channel)], message)
        else:
            self._publish(self.subscriptions[str(channel)], message)
