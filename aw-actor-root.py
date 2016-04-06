#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
from actingweb import actor
from actingweb import auth
from actingweb import config

import webapp2
import on_aw_delete


class MainPage(webapp2.RequestHandler):

    def get(self, id):
        check = auth.auth(id)
        Config = config.config()
        if self.request.get('_method') == 'DELETE':
            if not check.checkCookieAuth(self, Config.root + '?_method=DELETE'):
                return
            self.delete(id)
            return
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        if not check.checkCookieAuth(self, '/'):
            return
        self.redirect(Config.root + myself.id + '/www')

    def delete(self, id):
        Config = config.config()
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        check = auth.auth(id)
        if not check.checkCookieAuth(self, Config.root):
            return
        on_aw_delete.on_aw_delete_actor(myself)
        myself.delete()
        self.response.set_status(204)
        return

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id><:/?>', MainPage, name='MainPage'),
], debug=True)
