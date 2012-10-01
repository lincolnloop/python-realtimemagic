# Idea

Realtime Magic is an abstraction on top of sockjs-tornado that aims to
make writing realtime web applications less about the interaction
between the different pieces and more about writing your application
code.

In short, it's a library for writing realtime (most likely pubsub)
servers by defining what should happen when a message is received and
writing monitors to act on server changes.

# Protocol

From the client point of view, you can send any message, but
traditionally you would want to send json objects for doing
publish/subscribe.

For this we use the following protocol:

 * To subscribe to a channel: `{"action": "subscribe", "payload":
   {"channel": channel} }`. The channel will be created if it doesn't
   exist
 * To unsubscribe from a channel: `{"action": "unsubscribe", "payload":
   {"channel": channel} }`.
 * To send a message: `{"action": "publish", "payload": {"channel":
   channel, "message": "hello!"} }`

## Javascript

There's javascript code included that makes this easier.

```
  var client = new realtimeMagic.Client('{% realtime_endpoint %}/pubsub/');
  {% endif %}

   client.onopen = function() {
       console.log('open');
       client.subscribe('the_channel');
   };
   client.onmessage = function(message) {
       console.log('received: ', message);
   };
   client.onclose = function() {
       console.log('close');
   };

   client.publish("the_channel", "I'm new to this channel");
```

# Usage

To use realtime-magic you need to write a realtime server.

## Simplest possible realtime server

```
from realtimemagic import RealTimeMagic

if __name__ == '__main__':
    rtm = RealTimeMagic()
    rtm.start()
```

This is a basic realtime pubsub server. To test it we can write some
javascript code as the one above and, on the browser's javascript
console, run:

```
client.publish('the_channel', 'hello from the console')
```

Which would allow us to see the message coming back through the
realtime channel we're subscribled to.

## Pubsub

This is all we need to do realtime pubsub. But if we need to do
something else besides sending the message to all the channels, we
need to add some more logic to the server.

### Push traps

We can define what happens when the client publishes a message by
adding a push_trap.

```
from realtimemagic import RealTimeMagic


def change_the_published_messages(conn, channel, message):
    conn.master.publish(channel, '[ %s ]' % message,
        async=False)  # No need to spawn a new thread
    return False  # Don't send the message

if __name__ == '__main__':
    rtm = RealTimeMagic()
    rtm.push_traps.append(change_the_published_messages)
    rtm.start()
```

ToDo: Rethink the push_trap api. Allow to modify everything and refeed
to the next trap.

ToDo: Add better docs here

### Monitors

You may also need to monitor things happening in your server and send
information to certain channels based on that. For this, we run monitors.

Monitors are functions that run in their own thread and process
information when needed.

Typically you would wait on information added to a queue like
redis. Realtime magic provides a postgres monitor. A redis one is
coming.

```
from realtimemagic.monitors.psql import PsqlMonitor

psql = PsqlMonitor(dsn='dbname=test user=test password=test host=test')

@psql.monitor('status') # define a postgres channel to monitor
def status_changes(notification, pubsub): #react when the data comes in
    try:
        print notification
        data = json.loads(notification.payload)
        pubsub.publish('client_channel', {'info1': data['some_info']})
    except Exception, e:
        logging.error(e)

if __name__ == '__main__':
    rtm = RealTimeMagic()
    rtm.monitors.append(status_changes)
```

ToDo: Add better docs here

### Authentication

You can write authenticators. RTM provides a Django authenticator.

```
from realtimemagic import RealTimeMagic

from realtimemagic.auth.contrib import DjangoAuthenticator, AuthenticationError

class MyAuthenticator(DjangoAuthenticator):
    def check(self, conn, channel):
        try:
            user = self.get_user(conn)
            obj = SomeObject.objects.get(id=channel)
            if not obj.user_can_access(user):
                raise AuthenticationError(self.error_message)
        except SomeObject.DoesNotExist:
            logging.info('Chatbot does not exist')
            raise AuthenticationError(self.error_message)

if __name__ == '__main__':
    rtm = RealTimeMagic()
    rtm.authenticators['default'].append(MyAuthenticator())
    rtm.start()

```

ToDo: Handling Cookies!

ToDo: Add better docs here

## On open

```
from realtimemagic import RealTimeMagic


def on_open(self, conn_info):
    self.subscribe({'channel': 'echo'})

if __name__ == '__main__':
    rtm = RealTimeMagic(local=False)
    rtm.openings.append(on_open)
    rtm.start()
```

## Handling Messages Manually

```
from realtimemagic import RealTimeMagic


def on_open(self, conn_info):
    self.subscribe({'channel': 'echo'})


def echo(conn, message):
    #conn.master.slow_stuff(5)
    conn.master.publish('echo', message)

if __name__ == '__main__':
    rtm = RealTimeMagic()
    rtm.openings.append(on_open)
    rtm.receivers.append(echo)
    rtm.start()
```

# Architechture

 * Tornado receiver
 * Messages handling work enqueued
 * PubSub info kept on a dict (better datastructure?)
 * Hooks everywhere: openers/authenticators/handlers/push_traps/closers

# Philosophy 

 * Just python
 * Unblock early
 * Don't overload the server (enqueue work)
 * Pipes everywhere! 

# Deployment

TBD. (HAProxy or nginx in front)

# Scaling

I haven't looked into this. Still figuring out deployment.

The general idea is: If there's need for scaling, run multiple
instances of the server (optionally on multiple machines) and have the
load balancer use the following policy:

 * New connections -> round robin (or similar)
 * Messages -> broadcast to all instances (each instance will handle
   the connections in them)

Note: Is this even possible? How does nginx/haproxy handle the
messages on an open connection? We might need another level of
indirection within realtime-magic.

# Considerations

 * Running on PyPY instead of CPython is **much** faster and more reliable.
 * Ideally this would run on sockjs-gevent. Looking forward to seeing
   that project completed!

# Tests

At the moment there are no automated tests for the project, but there
are a couple of examples that help show how realtime-magic is supposed
to work.

The tests are the following:

## slow 

Sends three messages that block on IO (a sleep request to
postresql). These requests are handled in parallel and the server
doesn't block while handling them. This way if each request takes 5
seconds, the time for the client to receive the responses should be 5
seconds + overhead, instead of 15 seconds + overhead (which is what
would happen if the server blocked).

To execute this go to `realtimemagic/tests/slow/` and execute

```
python -m SimpleHTTPServer 8080
```

to host the client and 

```
python server.py
```

to run the realtime server.

Going to http://localhost:8080/ should show the requests arriving
after ~5 seconds.

## stress

The purpose of the stress tests is to be able to benchmark the
behaviour of realtime-magic and compare it to a basic sockjs-tornado
server. The benchmark code is based on http://mrjoes.github.com/2011/12/15/sockjs-bench.html.

The benchmark only tests a basic broadcast server (which broadcasts
every message received to every client). To compile the client code I
used eclipse (there should be an ant script to make this easier). 

There are two servers. The first one, base.py is what was used in the
original benchmarks and is just a basic sockjs-tornado server. Note
that this server doesn't handle requests in parallel (so the previous
test would take 15 seconds instead of 5 here). The second one is
server.py, which is realtime-magic implementation.

To test the server execute it by running

```
pypy server.py  # or pypy base.py
```

and run the client by going to `/tests/stress/sock-benchmarking/client/bin` and running

```
java -jar client.jar sockjs localhost:9000 ../logs/ 1000
```

TBD: Some data and/or graphs.

# To-Do

 * Document
 * Add more monitors
   - Redis
 * Improve authentication
   - split checks into check_channel(self, conn, channel) and check_message(self, conn, message)
 * Add basic configuration (managed in __init__)
   - Make the endpoint and port configurable (instead of /pubsub and 9000)
 * Add control message to prevent timeouts (relevant when behind nginx)
 * Take the pubsub logic out of the main server. Make it a handler registered by default.
 * Optimize! (consider making json parsing faster. How many times do strings get parsed?)
 * Benchmark better (what about auth and other io?)
 * Add a zmq local receiver (and utility function) to send messages to
   the server. In the future we could query stats.
 * How do push traps and handlers relate? Need a generic solution.


