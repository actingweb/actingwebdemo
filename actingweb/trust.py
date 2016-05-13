import actor
from db import db
import datetime
import config

__all__ = [
    'trust',
]


class trust():

    def get(self, id, peerid):
        result = db.Trust.query(db.Trust.id == id, db.Trust.peerid == peerid).get()
        if result:
            self.trust = result
            self.id = id
            self.baseuri = result.baseuri
            self.secret = result.secret
            self.notify = result.notify
            self.desc = result.desc
            self.peerid = peerid
            self.type = result.type
            self.relationship = result.relationship
            self.active = result.active
        else:
            self.id = id
            self.peerid = peerid
            self.trust = None
            self.active = False

    def delete(self):
        if not self.trust:
            self.get(self.id, self.peerid)
        if not self.trust:
            return False
        self.trust.key.delete()

    def modify(self, baseuri='', secret='', desc='', active=False, notify=False):
        if not self.trust:
            return False
        if len(baseuri) > 0:
            self.baseuri = baseuri
            self.trust.baseuri = baseuri
        if len(secret) > 0:
            self.secret = secret
            self.trust.secret = secret
        if len(desc) > 0:
            self.desc = desc
            self.trust.desc = desc
        self.trust.active = active
        self.trust.notify = notify
        self.trust.put()
        return True

    def create(self, baseuri='', type='', relationship='', secret='', active=False, notify=False, desc=''):
        self.baseuri = baseuri
        self.type = type
        Config = config.config()
        if not relationship or len(relationship) == 0:
            self.relationship = Config.default_relationship
        else:
            self.relationship = relationship
        if not secret or len(secret) == 0:
            self.secret = Config.newToken()
        else:
            self.secret = secret
        self.notify = notify
        self.active = active
        if not desc:
            desc = ''
        self.desc = desc
        if self.trust:
            self.trust.baseuri = self.baseuri
            self.trust.type = self.type
            self.trust.relationship = self.relationship
            self.trust.secret = self.secret
            self.trust.active = self.active
            self.trust.notify = self.notify
            self.trust.desc = self.desc
        else:
            self.trust = db.Trust(id=self.id,
                                  peerid=self.peerid,
                                  baseuri=self.baseuri,
                                  type=self.type,
                                  relationship=self.relationship,
                                  secret=self.secret,
                                  active=self.active,
                                  notify=self.notify,
                                  desc=self.desc)
        self.trust.put()
        return True

    def __init__(self, id, peerid):
        self.last_response_code = 0
        self.last_response_message = ''
        if not id or not peerid:
            self.trust = None
            return
        if len(id) == 0 or len(peerid) == 0:
            self.trust = None
            return
        self.get(id, peerid)
