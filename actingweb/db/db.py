from google.appengine.ext import ndb

__all__ = [
    'Actor',
    'Property',
    'Trust',
    'Subscription',
]

class Actor(ndb.Model):
  id = ndb.StringProperty(required=True)
  creator = ndb.StringProperty()
  passphrase = ndb.StringProperty()
  trustee = ndb.StringProperty()


class Property(ndb.Model):
  id = ndb.StringProperty(required=True)
  name = ndb.StringProperty(required=True)
  value = ndb.TextProperty()
  
class Trust(ndb.Model):
  id = ndb.StringProperty(required=True)
  peerid = ndb.StringProperty(required=True)
  baseuri = ndb.StringProperty(required=True)
  secret = ndb.StringProperty(required=True)  
  desc = ndb.TextProperty()
  notify = ndb.BooleanProperty()

class Subscription(ndb.Model):
  id = ndb.StringProperty(required=True)
  peerid = ndb.StringProperty(required=True)
  subscription = ndb.StringProperty(required=True)
  callback = ndb.StringProperty()
  granularity = ndb.StringProperty()
  paths = ndb.StringProperty(repeated=True)
  