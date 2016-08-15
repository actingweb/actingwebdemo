import urllib
import actor
import trust
import logging
import time

import config
import oauth
import base64

__all__ = [
    'auth',
    'init_actingweb',
]

# This is where each path and subpath in actingweb is assigned an authentication type
# Fairly simple: /oauth is always oauth, /www can be either basic+trust or
# oauth through config.py, and everything else is basic+trust


def select_auth_type(path, subpath):
    conf = config.config()
    if path == 'oauth':
        return 'oauth'
    if path == 'www':
        return conf.www_auth
    return 'basic'

# Returns three objects {config, actor, auth} (actor is none if actor is
# not found; auth is none if not authenticated and response message is set if this occurs)


def init_actingweb(appreq=None, id=None, path='', subpath='', enforce_auth=True):
    conf = config.config()
    if id:
        myself = actor.actor(id)
    else:
        myself = None
    if not myself or not myself.id:
        if enforce_auth:
            appreq.response.set_status(404, "Actor not found")
        return (conf, None, None)
    fullpath = '/' + path + '/' + subpath
    type = select_auth_type(path=path, subpath=subpath)
    auth_obj = auth(id, type=type)
    if not auth_obj.checkAuthentication(appreq=appreq, path=fullpath, enforce_auth=enforce_auth) and enforce_auth:
        appreq.response.set_status(403, "Forbidden")
    return (conf, myself, auth_obj)


class auth():

    def __init__(self, id, type='basic'):
        self.actor = actor.actor(id)
        self.token = None
        self.cookie_redirect = None
        self.cookie = None
        self.type = type
        self.oauth = None
        self.trust = None
        # acl stores the actual verified credentials and access rights after
        # authentication and authorisation have been done
        self.acl = {
            "authenticated": False,  # Has authentication been verified and passed?
            "authorised": False,    # Has authorisation been done and appropriate acls set?
            "rights": '',           # "a", "r" (approve or reject)
            "relationship": None,     # E.g. creator, friend, admin, etc
            "peerid": '',           # Peerid if there is a relationship
            "approved": False,      # True if the peer is approved
        }
        Config = config.config()
        self.config = Config
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
                self.type = 'none'
        elif self.type == 'basic':
            self.token = self.actor.passphrase
            self.realm = Config.auth_realm

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
        if not result or (result and 'access_token' not in result):
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
        if not path:
            path = ''
        if not self.actor:
            return False
        if self.token:
            now = time.time()
            auth = appreq.request.cookies.get(self.cookie)
            if auth == self.token and now < (float(self.expiry) - 20.0):
                logging.debug('Authorization cookie header matches a valid token')
                self.acl["relationship"] = "creator"
                return True
            elif auth != self.token:
                self.actor.deleteProperty(self.property)
                logging.debug('Authorization cookie header does not match a valid token')
        if self.cookie_redirect:
            logging.debug('Cookie redirect already set!')
            return False
        self.actor.setProperty('cookie_redirect', self.actor.id + path)
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

    def checkBasicAuth(self, appreq, path, enforce_auth=True):
        if self.type != 'basic':
            return False
        if not self.token:
            logging.warn("Trying to do basic auth when no passphrase value can be found.")
            return False
        if not 'Authorization' in appreq.request.headers and enforce_auth:
            appreq.response.headers['WWW-Authenticate'] = 'Basic realm="' + self.realm + '"'
            appreq.response.set_status(401)
            appreq.response.out.write("Authorization required")
            return False
        else:
            if not enforce_auth:
                return False
            auth = appreq.request.headers['Authorization']
            (basic, token) = auth.split(' ')
            if basic.lower() != "basic":
                appreq.response.set_status(403)
                return False
            (username, password) = base64.b64decode(auth.split(' ')[1]).split(':')
            if username != self.actor.creator:
                appreq.response.set_status(403)
                return False
            if password != self.actor.passphrase:
                appreq.response.set_status(403)
                return False
            self.acl["relationship"] = "creator"
            return True

    def checkTokenAuth(self, appreq):
        if not 'Authorization' in appreq.request.headers:
            return None
        else:
            auth = appreq.request.headers['Authorization']
            (bearer, token) = auth.split(' ')
            if bearer.lower() != "bearer":
                return None
            new_trust = trust.trust(id=self.actor.id, token=token)
            if new_trust.trust:
                self.acl["relationship"] = new_trust.relationship
                self.acl["peerid"] = new_trust.peerid
                self.acl["approved"] = new_trust.approved
                return new_trust
            else:
                return None

    # NOTE that path is NOT used for actual authentication, it is just used
    # for redirect as part of the authentication process
    def checkAuthentication(self, appreq, path, enforce_auth=True):
        trust = self.checkTokenAuth(appreq)
        if trust:
            self.trust = trust
            self.token = trust.secret
            self.acl["authenticated"] = True
            return True
        if self.type == 'oauth':
            if self.checkCookieAuth(appreq=appreq, path=path):
                self.acl["authenticated"] = True
                return True
        if self.type == 'basic':
            if self.checkBasicAuth(appreq=appreq, path=path, enforce_auth=enforce_auth):
                self.acl["authenticated"] = True
                return True
        return False

    def authorise(self, path='', subpath='', method='', peerid='', approved=True):
        if len(self.acl["peerid"]) > 0 and approved and self.acl["approved"] == False:
            return False
        if self.acl["relationship"]:
            relationship = self.acl["relationship"].lower()
        else:
            relationship = ''
        method = method.upper()
        self.acl["authorised"] = True
        self.acl["rights"] = "r"
        if len(path) == 0:
            return False
        fullpath = path.lower() + '/' + subpath.lower()
        # ACLs: ('role', 'path', 'METHODS', 'access')
        logging.debug('Testing access for (' + relationship +
                      ' ' + self.acl["peerid"] + ') on (' + fullpath + ' ' + peerid + ') using method ' + method)
        for acl in self.config.access:
            if acl[0] == 'any' and not self.acl["authenticated"]:
                continue
            if len(acl[0]) > 0 and acl[0] != 'any' and acl[0] != relationship and acl[0] != 'owner':
                continue  # no match on relationship
            if acl[0] == relationship or acl[0] == 'any' or len(acl[0]) == 0 or (acl[0] == 'owner' and len(peerid) > 0 and self.acl["peerid"] == peerid):
                if fullpath.find(acl[1]) == 0:
                    if len(acl[2]) == 0 or acl[2].find(method) != -1:
                        self.acl["rights"] = acl[3]
                        logging.debug('Granted ' + acl[3] + ' access with ACL:' + str(acl))
                        return True
        return False
