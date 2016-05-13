#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
from actingweb import actor
from actingweb import config
from actingweb.db import db

import webapp2
import json

import os
from google.appengine.ext.webapp import template

# Load global configurations
Config = config.config()


class MainPage(webapp2.RequestHandler):

    def get(self, id, path):
        myself = actor.actor(id)

        if self.request.get('_method') == 'PUT':
            self.set(id, path, self.request.get('value').decode('utf-8'))
            return
        if not path:
            values = {
                'id': id,
                'type': Config.type,
                'version': Config.version,
                'desc': Config.desc,
                'info': Config.info,
                'trustee': myself.trustee,
                'raml': Config.raml,
                'aw_version': Config.aw_version,
                'aw_supported': Config.aw_supported,
                'aw_formats': Config.aw_formats,
            }
            out = json.dumps(values)
            self.response.write(out.encode('utf-8'))
            self.response.headers["Content-Type"] = "application/json"
            return

        elif path == 'id':
            out = id
        elif path == 'type':
            out = Config.type
        elif path == 'version':
            out = Config.version
        elif path == 'desc':
            out = Config.desc + myself.id
        elif path == 'info':
            out = Config.info
        elif path == 'trustee':
            out = myself.trustee
        elif path == 'raml':
            out = Config.raml
        elif path == 'actingweb/version':
            out = Config.aw_version
        elif path == 'actingweb/supported':
            out = Config.aw_supported
        elif path == 'actingweb/formats':
            out = Config.aw_formats
        else:
            self.response.set_status(404)
        self.response.write(out.encode('utf-8'))

application = webapp2.WSGIApplication([
    (r'/(.*)/meta/?(.*)', MainPage),
], debug=True)
