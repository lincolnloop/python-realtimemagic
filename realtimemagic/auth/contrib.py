import logging

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User, AnonymousUser

from realtimemagic.auth import Authenticator, AuthenticationError


class DjangoAuthenticator(Authenticator):
    error_message = 'User not authorized to join this channel'

    def get_user(self, conn):
        try:
            session_key = self.get_cookies(conn).get('sessionid')
            session = Session.objects.get(session_key=session_key)
            uid = session.get_decoded().get('_auth_user_id')
            return User.objects.get(pk=uid)
        except User.DoesNotExist:
            logging.info('Subscribing as AnonymousUser')
            return AnonymousUser()
        except Session.DoesNotExist:
            logging.error('Session %s does not exist' % session_key)
            logging.info('Subscribing as AnonymousUser')
            return AnonymousUser()
        except Exception, e:
            logging.error('An error occured. %s' % e)
            raise AuthenticationError('An error occured. %s' % e)
