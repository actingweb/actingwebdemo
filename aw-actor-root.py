#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
from actingweb import actor
from actingweb import auth
from actingweb import config

import webapp2
from on_aw import on_aw_delete
import json


class MainPage(webapp2.RequestHandler):

    def get(self, id):
        check = auth.auth(id, type='basic')
        Config = config.config()
        if self.request.get('_method') == 'DELETE':
            if not check.checkAuth(self, Config.root + '?_method=DELETE'):
                return
            self.delete(id)
            return
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        if not check.checkAuth(self, '/'):
            return
        pair = {
            'id': myself.id,
            'creator': myself.creator,
            'passphrase': myself.passphrase,
            'trustee': myself.trustee,
        }
        out = json.dumps(pair)
        self.response.write(out.encode('utf-8'))
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(200)

    def delete(self, id):
        Config = config.config()
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        check = auth.auth(id, type='basic')
        if not check.checkAuth(self, Config.root):
            return
        on_aw_delete.on_aw_delete_actor(myself)
        myself.delete()
        self.response.set_status(204)
        return

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id><:/?>', MainPage, name='MainPage'),
], debug=True)
