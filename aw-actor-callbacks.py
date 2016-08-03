#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
import logging
import json
from actingweb import actor
from actingweb import auth
from actingweb import config

import webapp2
from on_aw import on_aw_callbacks


class MainPage(webapp2.RequestHandler):

    def get(self, id, name):
        if self.request.get('_method') == 'PUT':
            self.put(id, name)
        if self.request.get('_method') == 'POST':
            self.post(id, name)
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='callbacks')
        if not myself or not check:
            return
        if not check.authorise(path='callbacks', subpath=name, method='GET'):
            self.response.set_status(403)
            return
        if not on_aw_callbacks.on_get_callbacks(myself, self, name):
            self.response.set_status(403, 'Forbidden')

    def put(self, id, name):
        self.post(id, name)

    def post(self, id, name):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='callbacks')
        if not myself or not check:
            return
        path = name.split('/')
        if path[0] == 'subscriptions':
            peerid = path[1]
            subid = path[2]
            if not check.authorise(path='callbacks', subpath='subscriptions', method='POST', peerid=peerid):
                self.response.set_status(403)
                return
            sub = myself.getSubscription(peerid=peerid, subid=subid, callback=True)
            if sub:
                try:
                    params = json.loads(self.request.body.decode('utf-8', 'ignore'))
                except:
                    self.response.set_status(405, "Error in json body")
                    return
                if on_aw_callbacks.on_post_subscriptions(myself=myself, req=self, sub=sub, peerid=peerid, data=params):
                    self.response.set_status(204, 'Found')
                else:
                    self.response.set_status(405, 'Processing error')
                return
            self.response.set_status(404, 'Not found')
            return
        if not check.authorise(path='callbacks', subpath=name, method='POST'):
            self.response.set_status(403)
            return
        if not on_aw_callbacks.on_post_callbacks(myself, self, name):
            self.response.set_status(403, 'Forbidden')

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/callbacks<:/?><name:(.*)>', MainPage, name='MainPage'),
], debug=True)
