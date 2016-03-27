#!/usr/bin/env python
#
import cgi
import wsgiref.handlers
from actingweb import actor
from actingweb import config
from actingweb.db import db

import webapp2

import os
from google.appengine.ext.webapp import template

# Load global configurations
Config=config.config()

class MainPage(webapp2.RequestHandler):
  def set(self,id,path,value):
    myself = actor.actor(id)

    # NOTE!!! Temporarily, just as a test, PUT request changes the global values of Config
    # THIS SHOULD NOT HAPPEN
    # Values should change per actor
    # However, this behavior is only useful for a generic proxy implementation.
    # I have skipped the full implementation (requires a new db object with actor id as key)
    if not path:
        self.response.set_status(404)
    elif path == 'type':
        Config.type = value
    elif path == 'version':
        Config.version = value
    elif path == 'desc':
        Config.desc = value
    elif path == 'trustee':
        myself.setTrustee(value)
    elif path == 'info':
        Config.info = value
    elif path == 'wadl':
        Config.wadl = value
    else:
        self.response.set_status(404)

  def get(self,id,path):
    myself = actor.actor(id)

    if self.request.get('_method') == 'PUT':
        self.set(id,path,self.request.get('value'))
        return
    if not path:
        template_values = {
                'type' : Config.type,
                'version': Config.version,
                'desc': Config.desc + myself.id,
                'info': Config.info,
                'wadl': Config.wadl,
                'trustee': myself.trustee,
                'aw_version': Config.aw_version,
                'aw_supported': Config.aw_supported,
                'aw_formats': Config.aw_formats,
        }
        path = os.path.join(os.path.dirname(__file__), 'aw-actor-meta.xml')
        self.response.write(template.render(path, template_values).encode('utf-8'))

    elif path == 'type':
        self.response.write(Config.type)
    elif path == 'version':
        self.response.write(Config.version)
    elif path == 'desc':
        self.response.write(Config.desc + myself.id)
    elif path == 'trustee':
        self.response.write(myself.trustee)
    elif path == 'info':
        self.response.write(Config.info)
    elif path == 'wadl':
        self.response.write(Config.wadl)
    elif path == 'actingweb/version':
        self.response.write(Config.aw_version)
    elif path == 'actingweb/supported':
        self.response.write(Config.aw_supported)
    elif path == 'actingweb/formats':
        self.response.write(Config.aw_formats)
    else:
        self.response.set_status(404)

def put(self, id, path):
    self.set(id, path, self.request.body())

application = webapp2.WSGIApplication([
  (r'/(.*)/meta/?(.*)', MainPage),
], debug=True)
