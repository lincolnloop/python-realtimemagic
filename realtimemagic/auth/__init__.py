

class AuthenticationError(Exception):
    pass


class Authenticator(object):
    def get_cookies(self, conn):
        if conn.cookies:
            return conn.cookies
        return conn.session.conn_info.cookies

    def check(self, conn, channel):
        raise NotImplementedError('Auth method not implemented')
