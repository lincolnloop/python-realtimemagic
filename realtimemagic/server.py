import sys
import threading
import logging

from collections import defaultdict

from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection

import tornado.options
tornado.options.parse_command_line()

from auth import AuthenticationError


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
        channel, message = (i.strip() for i in payload.split(' ', 1))
        self.authorize(channel)
        self.master.publish(channel, message)

    def authorize(self, channel):
        try:
            for authenticator in self.master.authenticators.get(channel, []):
                authenticator.check(self, channel)
            else:
                for authenticator in self.master.authenticators.get('default', []):
                    authenticator.check(self, channel)
        except AuthenticationError, e:
            logging.info(e)  # send control message
            self.close()
        except Exception, e:
            logging.error(e)

    def subscribe(self, channel):
        self.authorize(channel)
        subscriptions = self.master.subscriptions
        if channel not in subscriptions or self not in subscriptions[channel]:
            subscriptions[channel].append(self)
            logging.info('Subscribing %s to %s' % (self, channel))  # send control message

    def unsubscribe(self, channel):
        subscriptions = self.master.subscriptions
        logging.info('Unsubscribing %s from channel %s' % (self, channel))  # send control message
        if self in subscriptions[channel]:
            subscriptions[channel].remove(self)

    def on_message(self, message):
        logging.info('Received message %s' % message)
        try:
            command, payload = message.split(';', 1)
            if command in self.VALID_COMMANDS:
                getattr(self, command)(payload.strip())
        except Exception, e:
            logging.error(e)

    def on_close(self):
        logging.info('Unsubscribing %s' % self)
        subscriptions = self.master.subscriptions
        for channel in subscriptions.keys():
            if self in subscriptions[channel]:
                subscriptions[channel].remove(self)


class RealTimeMagic(object):
    monitors = []

    def __init__(self, *args, **kwargs):
        # Use a better datastructure for subscriptions
        # Consider a self-locking dict
        self.subscriptions = defaultdict(list)  # consider spawning threads
        # Authenticators can be a normal dict
        self.authenticators = defaultdict(list)
        self.local = kwargs.get('local', False)

    def start(self):
        PubSubRouter = SockJSRouter(PubSubConnection, '/pubsub',
            user_settings={'master': self})

        app = web.Application(PubSubRouter.urls)
        app.listen(9000)
        for monitor in self.monitors:
            t = threading.Thread(target=monitor, args=(self,))
            t.daemon = True
            t.start()
        t = threading.Thread(target=ioloop.IOLoop.instance().start)
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

    def publish(self, channel, message):
        """
        Should we update this to use thoonk or another queue? should it be
        threaded?
        """
        #Consider using a thread pool to send multiple messages in parallel.
        for ws in self.subscriptions[channel]:
            ws.send(message)
