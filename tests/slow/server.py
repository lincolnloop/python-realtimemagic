import logging
from realtimemagic import RealTimeMagic

#from realtimemagic.monitors.psql import PsqlMonitor
#from realtimemagic.auth.contrib import DjangoAuthenticator, AuthenticationError

#from django.conf import settings

#from snarl.apps.bots.models import ChatBot


# class BotBotAuthenticator(DjangoAuthenticator):
#     def check(self, conn, channel):
#         try:
#             user = self.get_user(conn)
#             #Assuming one chatbot joins only one channel. Might need to change in the future
#             bot = ChatBot.objects.get(id=channel)
#             if not bot.user_can_access(user):
#                 raise AuthenticationError(self.error_message)
#         except ChatBot.DoesNotExist:
#             logging.info('Chatbot does not exist')
#             raise AuthenticationError(self.error_message)


# logs = PsqlMonitor(dsn='dbname=%s user=%s password=%s host=%s' %
#     (settings.DATABASES['default']['NAME'],
#         settings.DATABASES['default']['USER'],
#         settings.DATABASES['default']['PASSWORD'],
#         settings.DATABASES['default']['HOST']))


# # To-do: Listen to redis directly. This is too complicated.
# @logs.monitor('logs')
# def log_changes(notification, pubsub):
#     try:
#         print notification
#         data = json.loads(notification.payload)
#         #Assuming one chatbot joins only one channel. Might need to change in the future
#         pubsub.publish(data['chatbot'], {u'username': data['username'],
#             u'message': data['message']})
#     except Exception, e:
#         logging.error(e)

def echo(conn, message):
    logging.info('echo receiver')
    conn.master.slow_stuff(5)
    conn.master.publish('echo', message)

if __name__ == '__main__':
    rtm = RealTimeMagic(local=False)
    rtm.receivers.append(echo)
    #rtm.monitors.append(log_changes)
    #rtm.authenticators['default'].append(BotBotAuthenticator())
    rtm.start()
