#!/usr/bin/env python
#
#from actingweb import actor

import webapp2

import logging

import json


class root_factory(webapp2.RequestHandler):

    def get(self):
        if self.request.get('_method') == 'POST':
            self.post()
            return
        if self.app.registry.get('config').ui:
            template_values = {
            }
            template = self.app.registry.get('template').get_template('aw-root-factory.html')
            self.response.write(template.render(template_values).encode('utf-8'))
        else:
            self.response.set_status(404)


