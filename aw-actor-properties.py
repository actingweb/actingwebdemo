#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
import json
import logging
from actingweb import actor
from actingweb import auth

import webapp2


class MainPage(webapp2.RequestHandler):

    def get(self, id, name):
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, 'Actor not found')
            return
        check = auth.auth(id)
        if not check:
            self.response.set_status(404, "Not found")
            return
        if not check.checkCookieAuth(self, '/properties'):
            return

        # if name is not set, this request URI was the properties root
        if not name:
            self.listall(myself)
            return
        if self.request.get('_method') == 'PUT':
            myself.setProperty(name, self.request.get('value'))
            self.response.set_status(204)
            return
        if self.request.get('_method') == 'DELETE':
            myself.deleteProperty(name)
            self.response.set_status(204)
            return
        lookup = myself.getProperty(name)
        if lookup.value:
            self.response.write(lookup.value)
            return
        self.response.set_status(404, "Property not found")
        return

    def listall(self, myself):
        properties = myself.getProperties()
        if not properties:
            self.response.set_status(404, "No properties")
            return
        pair = dict()
        for property in properties:
            pair[property.name] = property.value
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        return

    def put(self, id, name):
        myself = actor.actor(id)
        if myself.id:
            myself.setProperty(name, self.request.body())
            self.response.set_status(204)
        else:
            self.response.set_status(404, 'Actor not found')
            return

    def post(self, id, name):
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, 'Actor not found')
            return
        if self.request.get('property'):
            myself.setProperty(self.request.get('property'), self.request.get('value'))
        else:
            # if this was a post to root properties, allow a set of values encode in the POST body
            if len(name) == 0:
                for name, value in self.params.items():
                    myself.setProperty(name, value)
            else:
                self.response.set_status(500)
        self.response.set_status(204)

    def delete(self, id, name):
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, 'Actor not found')
            return
        myself.deleteProperty(name)
        self.response.set_status(204)

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/properties<:/?><name:(.*)>', MainPage, name='MainPage'),
], debug=True)
