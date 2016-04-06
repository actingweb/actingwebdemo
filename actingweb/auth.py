import urllib
import actor
import logging
import time

import config
import oauth

__all__ = [
    'auth',
]


class auth():

    def __init__(self, id, type='oauth'):
        self.actor = actor.actor(id)
        self.token = None
        self.cookie_redirect = None
        self.cookie = None
        self.type = type
        Config = config.config()
        if not self.actor.id:
            self.actor = None
            return
        if self.type == 'oauth':
            self.oauth = oauth.oauth()
            if self.oauth.enabled():
                self.property = 'oauth_token'
                self.token = self.actor.getProperty(self.property).value
                self.expiry = self.actor.getProperty('oauth_token_expiry').value
                self.refresh_expiry = self.actor.getProperty('oauth_refresh_token_expiry').value
                self.refresh_token = self.actor.getProperty('oauth_refresh_token').value
                self.cookie = 'oauth_token'
                if self.actor.getProperty('cookie_redirect').value:
                    self.cookie_redirect = Config.root + \
                        self.actor.getProperty('cookie_redirect').value
                else:
                    self.cookie_redirect = None
                self.redirect = Config.root + self.actor.id + '/oauth'
            else:
                self.oauth = None
                self.type = 'none'

    def processOAuthAccept(self, result):
        if not result:
            return None
        if not result['access_token']:
            logging.info('No token in response')
            return None
        now = time.time()
        self.token = result['access_token']
        self.actor.setProperty('oauth_token', self.token)
        self.expiry = str(now + result['expires_in'])
        self.actor.setProperty('oauth_token_expiry', self.expiry)
        if 'refresh_token' in result:
            self.refresh_token = result['refresh_token']
            self.refresh_expiry = str(now + result['refresh_token_expires_in'])
            self.actor.setProperty('oauth_refresh_token', self.refresh_token)
            self.actor.setProperty('oauth_refresh_token_expiry', self.refresh_expiry)

    def processOAuthCallback(self, code):
        if not code:
            return False
        if not self.oauth:
            logging.warn('Call to processOauthCallback() with oauth disabled.')
            return False
        result = self.oauth.oauthRequestToken(code)
        if 'access_token' not in result:
            logging.warn('No token in response')
            return False
        self.processOAuthAccept(result)
        return True

    def validateOAuthToken(self):
        if not self.token or not self.expiry:
            return self.oauth.oauthRedirectURI(state=self.actor.id)
        now = time.time()
        if now > (float(self.expiry) - 20.0):
            if now > (float(self.refresh_expiry) - 20.0):
                return self.oauth.oauthRedirectURI(state=self.actor.id)
        else:
            return ""
        result = self.oauth.oauthRefreshToken(self.refresh_token)
        self.processOAuthAccept(result)
        return ""

    # Called from a www page (browser access) to verify that a cookie has been
    # set to the actor's valid token.
    def checkCookieAuth(self, appreq, path):
        if not self.actor:
            return False
        # Test for other auth here and only return true if no auth is available
        if self.type == 'none':
            return True
        if self.token:
            now = time.time()
            auth = appreq.request.cookies.get(self.cookie)
            if auth == self.token and now < (float(self.expiry) - 20.0):
                logging.debug('Authorization cookie header matches a valid token')
                return True
            elif auth != self.token:
                self.actor.deleteProperty(self.property)
                logging.debug('Authorization cookie header does not match a valid token')
        self.actor.setProperty('cookie_redirect', '/' + self.actor.id + path)
        self.cookie_redirect = self.actor.id + path
        appreq.redirect(self.redirect)
        return False

    # Called after successful auth (through checkCookieAuth) to set the cookie with the token value
    def setCookieOnCookieRedirect(self, appreq):
        if not self.cookie_redirect:
            return False
        if not self.token:
            logging.warn("Trying to set cookie when no token value can be found.")
            return False
        logging.debug('Setting Authorization cookie: ' + str(self.token))
        appreq.response.set_cookie(self.cookie, str(self.token),
                                   max_age=1209600, path='/', secure=True)
        appreq.redirect(str(self.cookie_redirect))
        self.actor.deleteProperty('cookie_redirect')
        return True
