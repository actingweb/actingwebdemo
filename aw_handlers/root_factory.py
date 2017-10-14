#!/usr/bin/env python
#
from actingweb import actor

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

# TODO: post has not been adapted to aws
    def post(self):
        myself = actor.actor()
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            is_json = True
            if 'creator' in params:
                creator = params['creator']
            else:
                creator = ''
            if 'trustee_root' in params:
                trustee_root = params['trustee_root']
            else:
                trustee_root = ''
            if 'passphrase' in params:
                passphrase = params['passphrase']
            else:
                passphrase = ''
        except ValueError:
            is_json = False
            creator = self.request.get('creator')
            trustee_root = self.request.get('trustee_root')
            passphrase = self.request.get('passphrase')
        if not myself.create(url=self.request.url, creator=creator, passphrase=passphrase):
            self.response.set_status(400, 'Not created')
            logging.warn("Was not able to create new actor("+str(self.request.url) + " " +
                         str(creator) + ")")
            return
        if len(trustee_root) > 0:
            myself.setProperty('trustee_root', trustee_root)
        self.response.headers.add_header("Location", str(Config.root + myself.id))
        if Config.www_auth == 'oauth' and not is_json:
            self.redirect(Config.root + myself.id + '/www')
            return
        pair = {
            'id': myself.id,
            'creator': myself.creator,
            'passphrase': myself.passphrase,
        }
        if len(trustee_root) > 0:
            pair['trustee_root'] = trustee_root
        if Config.ui and not is_json:
            template = Template_env.get_template('aw-root-created.html')
            self.response.write(template.render(pair).encode('utf-8'))
            return
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(201, 'Created')
