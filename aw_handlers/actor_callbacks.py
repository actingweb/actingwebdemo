import logging
import json
from actingweb import auth

import webapp2
from on_aw import on_aw_callbacks


class actor_callbacks(webapp2.RequestHandler):

    def get(self, id, name):
        """Handles GETs to callbacks"""
        if self.request.get('_method') == 'PUT':
            self.put(id, name)
        if self.request.get('_method') == 'POST':
            self.post(id, name)
        (myself, check) = auth.init_actingweb(appreq=self,
                                              id=id,
                                              path='callbacks',
                                              add_response=False,
                                              config=self.app.registry.get('config')
                                              )
        if not myself or (check.response["code"] != 200 and check.response["code"] != 401):
            auth.add_auth_response(appreq=self, auth_obj=check)
            return
        if not check.checkAuthorisation(path='callbacks', subpath=name, method='GET'):
            self.response.set_status(403, 'Forbidden')
            return
        if not on_aw_callbacks.on_get_callbacks(myself=myself, req=self, auth=check, name=name):
            self.response.set_status(403, 'Forbidden')

    def put(self, id, name):
        """PUT requests are handled as POST for callbacks"""
        self.post(id, name)

    def delete(self, id, name):
        """Handles deletion of callbacks, like subscriptions"""
        (myself, check) = auth.init_actingweb(appreq=self,
                                              id=id,
                                              path='callbacks',
                                              config=self.app.registry.get('config'))
        if not myself or check.response["code"] != 200:
            return
        path = name.split('/')
        if path[0] == 'subscriptions':
            peerid = path[1]
            subid = path[2]
            if not check.checkAuthorisation(path='callbacks', subpath='subscriptions', method='DELETE', peerid=peerid):
                self.response.set_status(403, 'Forbidden')
                return
            sub = myself.getSubscriptionObj(peerid=peerid, subid=subid, callback=True)
            if sub:
                sub.delete()
                self.response.set_status(204, 'Deleted')
                return
            self.response.set_status(404, 'Not found')
            return
        if not check.checkAuthorisation(path='callbacks', subpath=name, method='DELETE'):
            self.response.set_status(403, 'Forbidden')
            return
        if not on_aw_callbacks.on_delete_callbacks(myself=myself, req=self, auth=check, name=name):
            self.response.set_status(403, 'Forbidden')

    def post(self, id, name):
        """Handles POST callbacks"""
        (myself, check) = auth.init_actingweb(appreq=self,
                                              id=id,
                                              path='callbacks',
                                              add_response=False,
                                              config=self.app.registry.get('config'))
        # Allow unauthenticated requests to /callbacks/subscriptions, so
        # do the auth check further below
        path = name.split('/')
        if path[0] == 'subscriptions':
            peerid = path[1]
            subid = path[2]
            sub = myself.getSubscription(peerid=peerid, subid=subid, callback=True)
            if sub and len(sub) > 0:
                logging.debug("Found subscription (" + str(sub) + ")")
                if not check.checkAuthorisation(path='callbacks', subpath='subscriptions', method='POST', peerid=peerid):
                    self.response.set_status(403, 'Forbidden')
                    return
                try:
                    params = json.loads(self.request.body.decode('utf-8', 'ignore'))
                except:
                    self.response.set_status(405, "Error in json body")
                    return
                if on_aw_callbacks.on_post_subscriptions(myself=myself, req=self, auth=check, sub=sub, peerid=peerid, data=params):
                    self.response.set_status(204, 'Found')
                else:
                    self.response.set_status(405, 'Processing error')
                return
            self.response.set_status(404, 'Not found')
            return
        if not myself or (check.response["code"] != 200 and check.response["code"] != 401):
            auth.add_auth_response(appreq=self, auth_obj=check)
            return
        if not check.checkAuthorisation(path='callbacks', subpath=name, method='POST'):
            self.response.set_status(403, 'Forbidden')
            return
        if not on_aw_callbacks.on_post_callbacks(myself=myself, req=self, auth=check, name=name):
            self.response.set_status(403, 'Forbidden')
