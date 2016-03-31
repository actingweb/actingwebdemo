#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
from actingweb import actor
from actingweb import auth
from actingweb import config

import webapp2
import logging

import os
from google.appengine.ext.webapp import template

import on_aw_www_paths


class MainPage(webapp2.RequestHandler):

    def get(self, id, path):

        Config = config.config()
        if not Config.ui:
            self.response.set_status(404, "Web interface is not enabled")
            return
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        check = auth.auth(id, redirect=Config.root + myself.id + '/oauth')
        if not check:
            self.response.set_status(404, "Not able to authenticate")
            return
        if not check.checkCookieAuth(self, '/www/' + path):
            return

        if not path or path == '':
            template_values = {
                'url': self.request.url,
                'id': id,
                'creator': myself.creator,
                'trustee': myself.trustee,
            }
            template_path = os.path.join(os.path.dirname(__file__), 'aw-actor-www-root.html')
            self.response.write(template.render(template_path, template_values).encode('utf-8'))
            return

        if path == 'init':
            template_values = {
                'id': myself.id,
            }
            template_path = os.path.join(os.path.dirname(__file__), 'aw-actor-www-init.html')
            self.response.write(template.render(template_path, template_values).encode('utf-8'))
            return
        if path == 'properties':
            properties = myself.getProperties()
            template_values = {
                'id': myself.id,
                'properties': properties,
            }
            template_path = os.path.join(os.path.dirname(__file__), 'aw-actor-www-properties.html')
            self.response.write(template.render(template_path, template_values).encode('utf-8'))
            return
        if path == 'property':
            lookup = myself.getProperty(self.request.get('name'))
            if lookup.value:
                template_values = {
                    'id': myself.id,
                    'property': lookup.name,
                    'value': lookup.value,
                    'qual': '',
                }
            else:
                template_values = {
                    'id': myself.id,
                    'property': lookup.name,
                    'value': 'Not set',
                    'qual': 'no',
                }
            template_path = os.path.join(os.path.dirname(__file__), 'aw-actor-www-property.html')
            self.response.write(template.render(template_path, template_values).encode('utf-8'))
            return
        output = on_aw_www_paths.on_www_paths(path, auth, myself)
        if output:
            self.response.write(output)
        else:
            self.response.set_status(404, "Not found")
        return

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/www<:/?><path:(.*)>', MainPage, name='MainPage'),
], debug=True)
