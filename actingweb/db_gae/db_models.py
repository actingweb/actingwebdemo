from google.appengine.ext import ndb

class PeerTrustee(ndb.Model):
    id = ndb.StringProperty(required=True)
    peerid = ndb.StringProperty(required=True)
    baseuri = ndb.StringProperty(required=True)
    type = ndb.StringProperty(required=True)
    passphrase = ndb.StringProperty(required=True)

