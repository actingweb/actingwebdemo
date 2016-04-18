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
        check = auth.auth(id, type='basic')
        if not check.checkAuth(self, '/properties'):
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
            self.response.write(lookup.value.encode('utf-8'))
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
            try:
                js = json.loads(property.value)
                pair[property.name] = js
            except ValueError:
                pair[property.name] = property.value
        out = json.dumps(pair)
        self.response.write(out.encode('utf-8'))
        self.response.headers["Content-Type"] = "application/json"
        return

    def put(self, id, name):
        myself = actor.actor(id)
        if myself.id:
            check = auth.auth(id, type='basic')
            if not check.checkAuth(self, '/properties'):
                return
            value = self.request.body.decode('utf-8', 'ignore')
            myself.setProperty(name, value)
            self.response.set_status(204)
        else:
            self.response.set_status(404, 'Actor not found')
            return

    def post(self, id, name):
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, 'Actor not found')
            return
        check = auth.auth(id, type='basic')
        if not check.checkAuth(self, '/properties'):
            return
        if len(name) > 0:
            self.response.set_status(405)
        pair = dict()
        if len(self.request.arguments()) > 0:
            for name in self.request.arguments():
                pair[name] = self.request.get(name)
                myself.setProperty(name, self.request.get(name))
        else:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            for key in params:
                pair[key] = params[key]
                if isinstance(params[key], dict):
                    text = json.dumps(params[key])
                else:
                    text = params[key]
                myself.setProperty(key, text)
        out = json.dumps(pair)
        self.response.write(out.encode('utf-8'))
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(201, 'Created')

    def delete(self, id, name):
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, 'Actor not found')
            return
        check = auth.auth(id, type='basic')
        if not check.checkAuth(self, '/properties'):
            return
        myself.deleteProperty(name)
        self.response.set_status(204)

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/properties<:/?><name:(.*)>', MainPage, name='MainPage'),
], debug=True)
