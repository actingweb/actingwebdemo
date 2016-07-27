#!/usr/bin/env python
#
from actingweb import actor
from actingweb import config
from actingweb import trust
from actingweb import auth

import webapp2

import os
from google.appengine.ext.webapp import template
import json


class rootHandler(webapp2.RequestHandler):
    """Handles requests to /subscription"""

    def get(self, id):
        if self.request.get('_method') == 'POST':
            self.post(id)
            return
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscription')
        if not myself or not check:
            return
        if not check.authorise(path='subscription', method='GET'):
            self.response.set_status(403)
            return
        peerid = self.request.get('peerid')
        target = self.request.get('target')
        subtarget = self.request.get('subtarget')

        subscriptions = myself.getSubscriptions(peerid=peerid, target=target, subtarget=subtarget)
        if not subscriptions:
            self.response.set_status(404, 'Not found')
            return
        pairs = []
        for sub in subscriptions:
            pairs.append({
                'peerid': sub.peerid,
                'subscriptionid': sub.subid,
                'target': sub.target,
                'subtarget': sub.subtarget,
                'granularity': sub.granularity,
            })
        out = json.dumps(pairs)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(200, 'Ok')

    def post(self, id):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscription')
        if not myself or not check:
            return
        if not check.authorise(path='subscription', method='POST', peerid=check.acl["peerid"]):
            self.response.set_status(403)
            return
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            if 'id' in params:
                peerid = params['id']
            else:
                self.response.set_status(400, 'No peer id in request')
                return
            if 'target' in params:
                target = params['target']
            else:
                target = ''
            if 'subtarget' in params:
                subtarget = params['subtarget']
            if 'granularity' in params:
                granularity = params['granularity']
            else:
                granularity = 'high'
        except ValueError:
            self.response.set_status(400, 'No json body')
            return
        if peerid != check.acl["peerid"]:
            logging.warn("Peer " + peerid +
                         " tried to create a subscription for peer " + check.acl["peerid"])
            self.response.set_status(403, 'Wrong peer id in request')
            return
        new_sub = myself.createSubscription(
            peerid=check.acl["peerid"], target=target, subtarget=subtarget, granularity=granularity)
        if not new_sub:
            self.response.set_status(500, 'Unable to create new subscription')
            return
        self.response.headers.add_header(
            "Location", str(Config.root + myself.id + '/subscription/' + new_sub.peerid + '/' + new_sub.subid))
        pair = {
            'subscriptionid': new_sub.subid,
            'target': new_sub.target,
            'subtarget': new_sub.subtarget,
            'granularity': new_sub.granularity,
        }
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(201, 'Created')


# Handling requests to /subscription/*, e.g. /subscription/<peerid>
class relationshipHandler(webapp2.RequestHandler):

    def get(self, id, peerid):
        self.response.set_status(404, "Not found")


class subscriptionHandler(webapp2.RequestHandler):
    """ Handling requests to specific subscriptions, e.g. /subscription/<peerid>/12f2ae53bd"""

    def get(self, id, peerid, subid):
        if self.request.get('_method') == 'PUT':
            self.put(id, peerid, subid)
            return
        if self.request.get('_method') == 'DELETE':
            self.delete(id, peerid, subid)
            return
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscription', subpath=peerid + '/' + subid)
        if not myself or not check:
            return
        if not check.authorise(path='subscription', subpath='<id>/<id>', method='GET', peerid=peerid):
            self.response.set_status(403)
            return

    def post(self, id, peerid, subid):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscription', subpath=peerid + '/' + subid)
        if not myself or not check:
            return
        if not check.authorise(path='subscription', subpath='<id>/<id>', method='GET', peerid=peerid):
            self.response.set_status(403)
            return

    def put(self, id, peerid, subid):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscription', subpath=peerid + '/' + subid)
        if not myself or not check:
            return
        if not check.authorise(path='subscription', subpath='<id>/<id>', method='GET', peerid=peerid):
            self.response.set_status(403)
            return

    def delete(self, id, peerid, subid):
        (Config, myself, check) = auth.init_actingweb(appreq=self,
                                                      id=id, path='subscription', subpath=peerid + '/' + subid)
        if not myself or not check:
            return
        if not check.authorise(path='subscription', subpath='<id>/<id>', method='GET', peerid=peerid):
            self.response.set_status(403)
            return

application = webapp2.WSGIApplication([
    webapp2.Route(r'/<id>/subscription<:/?>', rootHandler, name='rootHandler'),
    webapp2.Route(r'/<id>/subscription/<peerid><:/?>',
                  relationshipHandler, name='relationshipHandler'),
    webapp2.Route(r'/<id>/subscription/<peerid>/<subid><:/?>',
                  subscriptionHandler, name='subscriptionHandler'),
], debug=True)
