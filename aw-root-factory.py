#!/usr/bin/env python
#
from actingweb import actor
from actingweb.db import db
from actingweb import config

import webapp2

import os
from google.appengine.ext.webapp import template


class MainPage(webapp2.RequestHandler):

    def get(self):
        if self.request.get('_method') == 'POST':
            self.post()
            return
        Config = config.config()
        if Config.ui:
            template_values = {
            }
            path = os.path.join(os.path.dirname(__file__), 'aw-root-factory.html')
            self.response.write(template.render(path, template_values).encode('utf-8'))
        else:
            self.response.set_status(404)

    def post(self):
        myself = actor.actor()
        Config = config.config()
        myself.create(self.request.url, self.request.get('creator'),
                      self.request.get('passphrase'), self.request.get('trustee'))
        self.response.headers.add_header("Location", Config.root + myself.id)
        self.response.set_status(201, 'Created')

application = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)
