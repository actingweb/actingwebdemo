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
            self.peerid = result.peerid
            self.type = result.type
            self.relationship = result.relationship
            self.active = result.active
            self.verified = result.verified
            self.verificationToken = result.verificationToken
        else:
            self.id = id
            self.peerid = peerid
            self.trust = None
            self.active = False
            self.verified = False

    def getByToken(self, token):
        result = db.Trust.query(db.Trust.id == self.id, db.Trust.secret == token).get()
        if result:
            self.trust = result
            self.id = id
            self.baseuri = result.baseuri
            self.secret = result.secret
            self.notify = result.notify
            self.desc = result.desc
            self.peerid = result.peerid
            self.type = result.type
            self.relationship = result.relationship
            self.active = result.active
            self.verified = result.verified
            self.verificationToken = result.verificationToken
        else:
            self.id = id
            self.peerid = None
            self.trust = None
            self.active = False
            self.verified = False

    def delete(self):
        if not self.trust:
            self.get(self.id, self.peerid)
        if not self.trust:
            return False
        self.trust.key.delete()

    def modify(self, baseuri='', secret='', desc='', active=None, notify=None, verified=None, verificationToken=None):
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
        if active is not None:
            self.active = active
            self.trust.active = active
        if notify is not None:
            self.notify = notify
            self.trust.notify = notify
        if verified is not None:
            self.verified = verified
            self.trust.verified = verified
        if verificationToken is not None:
            self.verificationToken = verificationToken
            self.trust.verificationToken = verificationToken
        self.trust.put()
        return True

    def create(self, baseuri='', type='', relationship='', secret='', active=False, notify=False, verified=False, verificationToken='', desc=''):
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
            result = db.Trust.query(db.Trust.id == self.id, db.Trust.secret == secret).get()
            if result:
                return False
            self.secret = secret
        self.notify = notify
        self.active = active
        self.verified = verified
        if not verificationToken or len(verificationToken) == 0:
            self.verificationToken = Config.newToken()
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
            self.trust.verified = self.verified
            self.trust.verificationToken = self.verificationToken
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
                                  verified=self.verified,
                                  verificationToken=self.verificationToken,
                                  desc=self.desc)
        self.trust.put()
        return True

    def __init__(self, id, peerid=None, token=None):
        self.last_response_code = 0
        self.last_response_message = ''
        if not id or len(id) == 0:
            self.trust = None
            return
        if (not peerid or len(peerid) == 0) and (not token or len(token) == 0):
            self.trust = None
            return
        if token and len(token) > 0:
            self.id = id
            self.getByToken(token)
        else:
            self.get(id, peerid)
