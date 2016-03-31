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
        if self.request.get('_method') == 'DELETE':
            self.delete(id)
            return
        Config = config.config()
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        self.redirect(Config.root + myself.id + '/www')

    def delete(self, id):
        Config = config.config()
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        check = auth.auth(id, redirect=Config.root + myself.id + '/oauth?_method=DELETE')
        if not check:
            self.response.set_status(404, "Not found")
            return
        if not check.checkCookieAuth(self, Config.root):
            return
        on_aw_delete.on_aw_delete_actor(myself)
        myself.delete()
        self.response.set_status(204)
        return

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id><:/?>', MainPage, name='MainPage'),
], debug=True)
