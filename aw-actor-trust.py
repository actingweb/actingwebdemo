#!/usr/bin/env python
#
from actingweb import actor
from actingweb import config
from actingweb import trust

import webapp2

import os
from google.appengine.ext.webapp import template
import json


# Handling requests to trust/
class rootHandler(webapp2.RequestHandler):

    def get(self, id):
        if self.request.get('_method') == 'POST':
            self.post()
            return
        myself = actor.actor(id)
        Config = config.config()
        relationship = ''
        type = ''
        peerid = ''
        relationship = self.request.get('relationship')
        type = self.request.get('type')
        peerid = self.request.get('peerid')

        relationships = myself.getTrustRelationships(
            relationship=relationship, peerid=peerid, type=type)
        if not relationships:
            self.response.set_status(404, 'Not found')
            return
        pairs = []
        for rel in relationships:
            pairs.append({
                'baseuri': rel.baseuri,
                'id': myself.id,
                'peerid': rel.peerid,
                'relationship': rel.relationship,
                'active': rel.active,
                'notify': rel.notify,
                'type': rel.type,
                'desc': rel.desc,
                'secret': rel.secret,
            })
        out = json.dumps(pairs)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(200, 'Ok')

    def post(self, id):
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        Config = config.config()
        secret = ''
        desc = ''
        relationship = Config.default_relationship
        type = ''
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            is_json = True
            if 'url' in params:
                url = params['url']
            else:
                url = ''
            if 'secret' in params:
                secret = params['secret']
            if 'relationship' in params:
                relationship = params['relationship']
            if 'type' in params:
                type = params['type']
            if 'desc' in params:
                desc = params['desc']
        except ValueError:
            is_json = False
            url = self.request.get('url')
            secret = self.request.get('secret')
            relationship = self.request.get('relationship')
            type = self.request.get('type')
        if len(url) == 0:
            self.response.set_status(400, 'Missing peer URL')

        new_trust = myself.createTrust(
            url=url, secret=secret, desc=desc, relationship=relationship, type=type)
        if not new_trust:
            self.response.set_status(500, 'Unable to create trust relationship')
            return
        self.response.headers.add_header(
            "Location", str(Config.root + myself.id + '/trust/' + new_trust.relationship + '/' + new_trust.peerid))
        pair = {
            'baseuri': new_trust.baseuri,
            'id': myself.id,
            'peerid': new_trust.peerid,
            'relationship': new_trust.relationship,
            'active': new_trust.active,
            'notify': new_trust.notify,
            'type': new_trust.type,
            'desc': new_trust.desc,
            'secret': new_trust.secret,
        }
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(201, 'Created')


# Handling requests to /trust/*, e.g. /trust/friend
class relationshipHandler(webapp2.RequestHandler):

    def get(self, id, relationship):
        if self.request.get('_method') == 'POST':
            self.post()
            return
        self.response.set_status(404, "Not found")

    def post(self, id, relationship):
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        Config = config.config()
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            if 'baseuri' in params:
                baseuri = params['baseuri']
            else:
                baseuri = ''
            if 'id' in params:
                peerid = params['id']
            else:
                peerid = ''
            if 'type' in params:
                type = params['type']
            else:
                type = ''
            if 'secret' in params:
                secret = params['secret']
            else:
                secret = ''
            if 'desc' in params:
                desc = params['desc']
            else:
                desc = ''
            notify = False
            if 'notify' in params:
                if str(params['notify']).lower() == 'true':
                    notify = True
        except ValueError:
            self.response.set_status(400, 'No json content')
            return

        if len(baseuri) == 0 or len(peerid) == 0 or len(type) == 0:
            self.response.set_status(400, 'Missing mandatory attributes')
            return

        if relationship.lower() != Config.default_relationship.lower() or not Config.auto_accept_default_relationship:
            # Do further validation
            self.response.set_status(403, 'Forbidden')
            return
        new_trust = trust.trust(myself.id, peerid)
        if new_trust.trust:
            self.response.set_status(403, 'Forbidden')
            return
        new_trust.create(baseuri=baseuri, secret=secret, type=type,
                         relationship=relationship, active=True, notify=notify, desc=desc)
        self.response.headers.add_header(
            "Location", str(Config.root + myself.id + '/trust/' + new_trust.relationship + "/" + new_trust.peerid))
        pair = {
            'baseuri': new_trust.baseuri,
            'id': myself.id,
            'peerid': new_trust.peerid,
            'relationship': new_trust.relationship,
            'active': new_trust.active,
            'notify': new_trust.notify,
            'type': new_trust.type,
            'desc': new_trust.desc,
            'secret': new_trust.secret,
        }
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(201, 'Created')


# Handling requests to specific relationships, e.g. /trust/friend/12f2ae53bd
class trustHandler(webapp2.RequestHandler):

    def get(self, id, relationship, peerid):
        if self.request.get('_method') == 'PUT':
            self.put()
            return
        if self.request.get('_method') == 'DELETE':
            self.delete()
            return
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        Config = config.config()
        my_trust = trust.trust(myself.id, peerid)
        if not my_trust.trust or my_trust.relationship.lower() != relationship.lower():
            self.response.set_status(404, 'Not found')
            return
        pair = {
            'baseuri': my_trust.baseuri,
            'id': myself.id,
            'peerid': my_trust.peerid,
            'relationship': my_trust.relationship,
            'active': my_trust.active,
            'notify': my_trust.notify,
            'type': my_trust.type,
            'desc': my_trust.desc,
            'secret': my_trust.secret,
        }
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(200, 'Ok')

    def put(self, id, relationship, peerid):
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        Config = config.config()
        my_trust = trust.trust(myself.id, peerid)
        if not my_trust or my_trust.relationship.lower() != relationship.lower():
            self.response.set_status(404, 'Not found')
            return
        try:
            change = False
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            if 'baseuri' in params:
                change = True
                baseuri = params['baseuri']
            else:
                baseuri = ''
            if 'secret' in params:
                change = True
                secret = params['secret']
            else:
                secret = ''
            if 'desc' in params:
                change = True
                desc = params['desc']
            else:
                desc = ''
        except ValueError:
            self.response.set_status(400, 'No json content')
            return
        if not change:
            self.response.set_status(405, 'Not modified')
            return
        if my_trust.modify(baseuri=baseuri, secret=secret, desc=desc):
            self.response.set_status(204, 'Ok')
        else:
            self.response.set_status(405, 'Not modified')

    def delete(self, id, relationship, peerid):
        myself = actor.actor(id)
        if not myself.id:
            self.response.set_status(404, "Actor not found")
            return
        Config = config.config()
        my_trust = trust.trust(myself.id, peerid)
        if not my_trust.trust or my_trust.relationship.lower() != relationship.lower():
            self.response.set_status(404, 'Not found')
            return
        isPeer = self.request.get('peer')
        if isPeer.lower() == "true":
            deleted = myself.deleteTrust(peerid, deletePeer=False)
        else:
            deleted = myself.deleteTrust(peerid, deletePeer=True)
        if not deleted:
            self.response.set_status(500, 'Not able to delete relationship with peer.')
            return
        self.response.set_status(204, 'Ok')


application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/trust<:/?>', rootHandler, name='rootHandler'),
    webapp2.Route(r'/<id>/trust/<relationship><:/?>',
                  relationshipHandler, name='relationshipHandler'),
    webapp2.Route(r'/<id>/trust/<relationship>/<peerid><:/?>', trustHandler, name='trustHandler'),
], debug=True)
