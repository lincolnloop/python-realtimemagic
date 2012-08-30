Example ussage

```
@syntax: python
from realtimemagic import RealTimeMagic

from realtimemagic.monitors.psql import PsqlMonitor
from realtimemagic.auth.contrib import DjangoAuthenticator, AuthenticationError

from django.conf import settings

from snarl.apps.bots.models import ChatBot


class BotBotAuthenticator(DjangoAuthenticator):
    def check(self, conn, channel):
        try:
            user = self.get_user(conn)
            #Assuming one chatbot joins only one channel. Might need to change in the future
            bot = ChatBot.objects.get(id=channel)
            if not bot.user_can_access(user):
                raise AuthenticationError(self.error_message)
        except ChatBot.DoesNotExist:
            raise AuthenticationError(self.error_message)


logs = PsqlMonitor(dsn='dbname=snarl user=snarl')


# To-do: Listen to redis directly. This is too complicated.
@logs.monitor('logs')
def log_changes(notification, pubsub):
    print notification
    chatbot, username, message = notification.payload.split('=>', 2)
    #Assuming one chatbot joins only one channel. Might need to change in the future
    pubsub.publish(chatbot, {'username': username,
        'message': message})

if __name__ == '__main__':
    rtm = RealTimeMagic(local=settings.DEBUG)
    rtm.monitors.append(log_changes)
    rtm.authenticators['logs'].append(DjangoAuthenticator())
    rtm.start()
```
