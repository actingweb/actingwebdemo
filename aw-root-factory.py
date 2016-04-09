#!/usr/bin/env python
#
from actingweb import actor
from actingweb.db import db
from actingweb import config

import webapp2

import os
from google.appengine.ext.webapp import template
import json


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
        creator = self.request.get('creator')
        passphrase = self.request.get('passphrase')
        trustee = self.request.get('trustee')
        if len(creator) == 0 and len(passphrase) == 0 and len(trustee) == 0:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            if 'creator' in params:
                creator = params['creator']
            if 'passphrase' in params:
                passphrase = params['passphrase']
            if 'trustee' in params:
                trustee = params['trustee']
        myself.create(url=self.request.url, creator=creator,
                      passphrase=passphrase, trustee=trustee)
        self.response.headers.add_header("Location", Config.root + myself.id)
        pair = {
            'id': myself.id,
            'creator': myself.creator,
            'passphrase': myself.passphrase,
            'trustee': myself.trustee,
        }
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(201, 'Created')

application = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)
