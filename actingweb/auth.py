import urllib
import actor
import logging
import json
import time
from google.appengine.api import urlfetch

import config

__all__ = [
    'oauth',
    'auth',
]

# This function code is from latest urlfetch. For some reason the Appengine version of urlfetch does not include links()
def PaginationLinks(self):
    """Links parsed from HTTP Link header"""
    ret = []
    if 'link' in self.headers:
        linkheader = self.headers['link']
    else:
        return ret
    for i in linkheader.split(','):
        try:
            url, params = i.split(';', 1)
        except ValueError:
            url, params = i, ''
        link = {}
        link['url'] = url.strip('''<> '"''')
        for param in params.split(';'):
            try:
                k, v = param.split('=')
            except ValueError:
                break
            link[k.strip(''' '"''')] = v.strip(''' '"''')
        ret.append(link)
    return ret

class oauth():
    def __init__(self, token = None):
        self.config = config.config()
        self.response_type="code"
        self.grant_type="authorization_code"
        self.refresh_type="refresh_token"
        self.token=token
        self.first=None
        self.next=None
        self.prev=None
        self.last_response_code=0
        self.last_response_message=""
        # Hack to get access to GAE default logger
        logging.getLogger().handlers[0].setLevel(self.config.logLevel)

    def setToken(self, token):
        if token:
            self.token=token

    def postRequest(self, url, params = None, cleartoken = False):
        if cleartoken:
            self.token = None
        if params:
            data = json.dumps(params)
            logging.info('Oauth POST request with JSON payload: '+url+'?'+data)
        else:
            data = None
            logging.info('Oauth POST request: '+url)
        if self.token:
            headers = {'Content-Type': 'application/json',
                        'Authorization': 'Bearer '+self.token,
                      }
        else:
            headers = {'Content-Type': 'application/json'}
        response = urlfetch.fetch(url=url, payload=data, method=urlfetch.POST, headers=headers)
        self.last_response_code = response.status_code
        self.last_response_message = response.content
        if response.status_code == 204:
            return True
        if response.status_code != 200:
            logging.info('Error when sending POST request: '+str(response.status_code)+response.content)
            return False
        logging.debug('Oauth POST response JSON:'+response.content)
        return json.loads(response.content)

    def getRequest(self, url, params = None):
        if not self.token:
            return None
        if params:
            url = url+'?'+urllib.urlencode(params)
        logging.info('Oauth GET request: '+url)
        urlfetch.set_default_fetch_deadline(60)
        response = urlfetch.fetch(url=url,
            method=urlfetch.GET,
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer '+self.token}
            )
        self.last_response_code = response.status_code
        self.last_response_message = response.content
        if response.status_code < 200 or response.status_code > 299:
            logging.info('Error when sending GET request to Oauth: '+str(response.status_code)+response.content)
            return False
        links = PaginationLinks(response)
        for link in links:
            logging.debug('Links:'+link['rel']+':'+link['url'])
            if link['rel'] == 'next':
                self.next = link['url']
            elif link['rel'] == 'first':
                self.first = link['url']
            elif link['rel'] == 'prev':
                self.prev = link['url']
        return json.loads(response.content)

    def deleteRequest(self, url):
        if not self.token:
            return None
        logging.info('Oauth DELETE request: '+url)
        response = urlfetch.fetch(url=url,
            method=urlfetch.DELETE,
            headers={'Content-Type': 'application/json',
                     'Authorization': 'Bearer '+self.token}
            )
        self.last_response_code = response.status_code
        self.last_response_message = response.content
        if response.status_code < 200 and response.status_code>299:
            logging.info('Error when sending DELETE request to Oauth: '+str(response.status_code)+response.content)
            return False
        if response.status_code == 204:
            return True
        return json.loads(response.content)

    def oauthRedirectURI(self, state=''):
        params = {
            'response_type': self.response_type,
            'client_id': self.config.oauth['client_id'],
            'redirect_uri': self.config.oauth['redirect_uri'],
            'scope': self.config.oauth['scope'],
            'state': state,
        }
        uri=self.config.oauth['auth_uri']+"?"+urllib.urlencode(params)
        logging.info('OAuth redirect with url: '+uri+' and state:'+state)
        return uri

    def oauthRequestToken(self, code = None):
        if not code:
            return None
        params = {
            'grant_type': self.grant_type,
            'client_id': self.config.oauth['client_id'],
            'client_secret': self.config.oauth['client_secret'],
            'code': code,
            'redirect_uri': self.config.oauth['redirect_uri'],
        }
        result = self.postRequest(url = self.config.oauth['token_uri'], cleartoken = True, params = params)
        self.token = result['access_token']
        return result

    def oauthRefreshToken(self, refresh_token):
        if not refresh_token:
            return None
        params = {
            'grant_type': self.refresh_type,
            'client_id': self.config.oauth['client_id'],
            'client_secret': self.config.oauth['client_secret'],
            'refresh_token': refresh_token,
        }
        result = self.postRequest(url = self.config.oauth['token_uri'], cleartoken = True, params = params)
        if not result:
            self.token = None
            return False
        self.token = result['access_token']
        return result

class auth():
    def __init__(self, id, type='oauth', redirect=''):
        self.config = config.config()
        self.actor = actor.actor(id)
        self.type = type
        if type == 'oauth':
            self.property = 'oauth_token'
            self.token=self.actor.getProperty('oauth_token').value
            self.expiry = self.actor.getProperty('oauth_token_expiry').value
            self.cookie = 'oauth_token'
        else:
            # Add more authorization types here
            self.token = 'Unknown'
        if redirect != '':
            self.redirect = redirect
        else:
            self.redirect = self.config.root+self.actor.id+'/oauth'
        if not self.actor.id:
            self.actor = None
            return None

    def checkCookieAuth(self, appreq, path):
        if not self.actor:
            return False
        if self.token:
            now = time.time()
            auth=appreq.request.cookies.get(self.cookie)
            if auth == self.token and now < (float(self.expiry)-20.0):
                logging.debug('Authorization cookie header matches a valid actor token')
                return True
            elif auth != self.token:
                    self.actor.deleteProperty(self.property)
                    logging.debug('Authorization cookie header does not match a valid actor token')
        params = {
            'cookie_redirect': self.actor.id+path,
        }
        appreq.redirect(self.redirect+'?'+urllib.urlencode(params))
        return False
