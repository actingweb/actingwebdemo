#!/usr/bin/env python
import webapp2
import logging
import time
from actingweb import actor
from actingweb import auth
from actingweb import config
import on_aw_oauth

class MainPage(webapp2.RequestHandler):

    def get(self,id,path):
        myself = actor.actor(id)
        Config=config.config()
        if not myself.id:
            self.response.set_status(404, "Actor Not Found")
            return
        now = time.time()
        oauth=auth.oauth()
        if not oauth.enabled():
            self.response.set_status(403, "OAuth not enabled")
            return
        # Handle callback from oauth granter
        if self.request.get('code'):
            code=self.request.get('code')
            result = oauth.oauthRequestToken(code)
            if not result:
                self.response.set_status(502, "OAuth Token Request Failed")
                return
            else:
                # Even if oauth is successful, we need to validate that the identity that did the oauth is identical
                # to the original identity that was bound to this actor.
                # The check_on_oauth_success() function returns False if identity (or anything else) is wrong.
                if not on_aw_oauth.check_on_oauth_success(myself, oauth, result):
                    logging.info('Forbidden identity.')
                    self.response.set_status(403, "Forbidden to this identity")
                    return
        else:
            # No callback, we need to verify valid token or get a new one or refresh
            token = myself.getProperty('oauth_token')
            if self.request.get('cookie_redirect'):
                myself.setProperty('aw_tmp_redirect', self.request.get('cookie_redirect'))
                myself.setProperty('aw_auth_type', 'cookie')
            expiry = myself.getProperty('oauth_token_expiry').value
            if not token.value or not expiry:
                self.redirect(oauth.oauthRedirectURI(state = myself.id))
                return
            if now > (float(expiry)-20.0):
                expiry2 = myself.getProperty('oauth_refresh_token_expiry').value
                if now > (float(expiry2)-20.0):
                    self.redirect(oauth.oauthRedirectURI(state = myself.id))
                    return
            result = oauth.oauthRefreshToken(myself.getProperty('oauth_refresh_token').value)
            if not result:
                logging.info("OAuth token refresh failed")
                self.redirect(oauth.oauthRedirectURI(state = myself.id))
                return
        if not result['access_token']:
            self.response.set_status(502, "OAuth Token Request/Refresh Succeded, but no token in response.")
            return
        myself.setProperty('oauth_token', result['access_token'])
        myself.setProperty('oauth_token_expiry', str(now+result['expires_in']))
        if 'refresh_token' in result:
            myself.setProperty('oauth_refresh_token', result['refresh_token'])
            myself.setProperty('oauth_refresh_token_expiry', str(now+result['refresh_token_expires_in']))
        redirect=myself.getProperty('aw_tmp_redirect')
        if redirect.value:
            aw_auth_type=myself.getProperty('aw_auth_type')
            myself.deleteProperty('aw_tmp_redirect')
            if aw_auth_type.value == 'cookie':
                logging.info('Setting Authorization cookie:'+result['access_token'])
                self.response.set_cookie('oauth_token', str(result['access_token']), max_age=1209600, path='/',
                                        secure=True)
                self.redirect(str(Config.root+redirect.value))
                return
            else:
                logging.info('Invalid authentication type:'+aw_auth_type.value)
                self.response.set_status(403, "Invalid authentication type")
                return
        self.response.set_status(204, "OAuthorization Done")
        return

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/oauth<:/?><path:.*>', MainPage, name='MainPage'),
], debug=True)
