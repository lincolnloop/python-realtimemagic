import logging

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User, AnonymousUser

from realtimemagic.auth import Authenticator, AuthenticationError


class DjangoAuthenticator(Authenticator):
    error_message = 'User not authorized to join this channel'

    def get_user(self, conn):
        try:
            logging.info(self.get_cookies(conn))
            session_key = self.get_cookies(conn).get('sessionid')
            logging.info(session_key)
            if 'Set-Cookie:' in session_key:
                # Horrible hack
                cookies = dict(i.split('=') for i in session_key.split('Set-Cookie:'))
                session_key = cookies.get('sessionid')
                logging.info('updating session key to %s' % session_key)
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
