Example ussage

```
from realtimemagic import RealTimeMagic

from realtimemagic.monitors.psql import PsqlMonitor
from realtimemagic.auth.contrib import DjangoAuthenticator, AuthenticationError

from django.conf import settings

from myapp.models import Something


class MyAppAuthenticator(DjangoAuthenticator):
    def check(self, conn, channel):
        try:
            user = self.get_user(conn)
            
            obj = Something.objects.get(id=channel)
            if not obj.user_can_access(user):
                raise AuthenticationError(self.error_message)
        except Something.DoesNotExist:
            raise AuthenticationError(self.error_message)


logs = PsqlMonitor(dsn='dbname=test user=test')


# To-do: Listen to redis directly. This is too complicated.
@logs.monitor('logs')
def log_changes(notification, pubsub):
    print notification
    channel, message = notification.payload.split('=>', 1)
    pubsub.publish(channel, {'message': message})

if __name__ == '__main__':
    rtm = RealTimeMagic(local=settings.DEBUG)
    rtm.monitors.append(log_changes)
    rtm.authenticators['logs'].append(DjangoAuthenticator())
    rtm.start()
```


# To-Do

 * Document
 * Add more monitors
   - Redis
 * Improve authentication
   - split checks into check_channel(self, conn, channel) and check_message(self, conn, message)
 * Add a JS API
 * Add the possibility of opening a connection (registering receivers for messages)
 * Add control messages on pub/sub/close/etc
 * Add basic configuration (managed in __init__)
 * Add control message to prevent timeouts (relevant when behind nginx)
 * Add signals on channel created/destroyed



