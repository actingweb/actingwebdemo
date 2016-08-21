#!/usr/bin/env python
import webapp2
import logging
from actingweb import actor
from actingweb import auth
from actingweb import config
from on_aw import on_aw_oauth


class MainPage(webapp2.RequestHandler):

    def get(self, id, path):
        (Config, myself, my_auth) = auth.init_actingweb(appreq=self,
                                                        id=id, path='oauth', subpath=path)
        if not myself or not my_auth:
            return
        if not check.authorise(path='oauth', subpath=path, method='GET'):
            self.response.set_status(403)
            return
        if my_auth.type != 'oauth':
            self.response.set_status(403, "OAuth not enabled")
            return
        # Handle callback from oauth granter
        if self.request.get('code'):
            if not my_auth.processOAuthCallback(self.request.get('code')):
                self.response.set_status(502, "OAuth Token Request Failed")
                return
            else:
                # Even if oauth is successful, we need to validate that the identity that did the oauth is identical
                # to the original identity that was bound to this actor.
                # The check_on_oauth_success() function returns False if identity (or
                # anything else) is wrong.
                if not on_aw_oauth.check_on_oauth_success(myself, token=my_auth.token):
                    logging.info('Forbidden identity.')
                    self.response.set_status(403, "Forbidden to this identity")
                    return

        redirect_uri = my_auth.validateOAuthToken()
        if len(redirect_uri) > 0:
            self.redirect(redirect_uri)
            return
        if len(redirect_uri) == 0:
            if my_auth.setCookieOnCookieRedirect(self):
                return
            self.response.set_status(204, "OAuthorization Done")
            return
        logging.info("OAuth token refresh failed")
        return


application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/oauth<:/?><path:.*>', MainPage, name='MainPage'),
], debug=True)
