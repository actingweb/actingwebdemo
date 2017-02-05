from google.appengine.ext import ndb

class PeerTrustee(ndb.Model):
    id = ndb.StringProperty(required=True)
    peerid = ndb.StringProperty(required=True)
    baseuri = ndb.StringProperty(required=True)
    type = ndb.StringProperty(required=True)
    passphrase = ndb.StringProperty(required=True)


class Subscription(ndb.Model):
    id = ndb.StringProperty(required=True)
    peerid = ndb.StringProperty(required=True)
    subid = ndb.StringProperty(required=True)
    granularity = ndb.StringProperty()
    target = ndb.StringProperty()
    subtarget = ndb.StringProperty()
    resource = ndb.StringProperty()
    seqnr = ndb.IntegerProperty(default=1)
    callback = ndb.BooleanProperty()


class SubscriptionDiff(ndb.Model):
    id = ndb.StringProperty(required=True)
    subid = ndb.StringProperty(required=True)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    diff = ndb.TextProperty()
    seqnr = ndb.IntegerProperty()
