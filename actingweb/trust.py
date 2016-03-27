import actor
from db import db
import datetime

__all__ = [
    'trust',
]

class trust():
  def get(self, id, peerid):
    result = db.Trust.query(db.Trust.id == id, db.Trust.peerid == peerid).fetch()
    if result:
        self.id = id
        self.baseuri = baseuri
        self.secret = secret
        self.notify = notify
        self.desc = desc
        self.trustid = trustid
    else:
        self.id = None

  def delete(self):
    result = db.Trust.query(db.Trust.id == id, db.Trust.peerid == peerid).fetch()
    if result:
        result.delete()

  def create(self, baseuri, secret, notify, desc):
    self.baseuri = baseuri
    self.secret = secret
    self.notify = notify
    self.desc = desc
    trust = db.Trust(id = self.id,
                     peerid = self.peerid,
                    baseuri = baseuri,
                    secret = secret,
                    notify = notify,
                    desc = desc)
    trust.put()

  def __init__(self, id='', peerid=''):
    self.get(id, peerid)
