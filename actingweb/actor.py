from db import db
import datetime
import property
import urllib
import config
import trust

__all__ = [
    'actor',
]


def getPeerInfo(self, url):
    response = urlfetch.fetch(url=url + 'meta',
                              method=urlfetch.GET
                              )
    self.last_response_code = response.status_code
    self.last_response_message = response.content
    return json.loads(response.content)


class actor():

    def get(self, id):
        result = db.Actor.query(db.Actor.id == id).get()
        if result:
            self.id = id
            self.creator = result.creator
            self.passphrase = result.passphrase
            self.trustee = result.trustee
        else:
            self.id = None

    def create(self, url, creator, passphrase, trustee):
        seed = url
        now = datetime.datetime.now()
        seed += now.strftime("%Y%m%dT%H%M%S")
        if len(creator) > 0:
            self.creator = creator
        else:
            self.creator = "creator"

        Config = config.config()
        if passphrase and len(passphrase) > 0:
            self.passphrase = passphrase
        else:
            self.passphrase = Config.newToken()
        self.id = Config.newUUID(seed)
        if len(trustee) > 0:
            self.trustee = trustee
        else:
            self.trustee = ""
        actor = db.Actor(creator=self.creator,
                         passphrase=self.passphrase,
                         id=self.id,
                         trustee=self.trustee)
        actor.put()

    def delete(self):
        properties = self.getProperties()
        for prop in properties:
            prop.key.delete()
        relationships = self.getTrustRelationships()
        for rel in relationships:
            rel.key.delete()
        result = db.Actor.query(db.Actor.id == self.id).get()
        if result:
            result.key.delete()

    def setProperty(self, name, value):
        prop = property.property(self, name)
        prop.set(value)

    def getProperty(self, name):
        prop = property.property(self, name)
        return prop

    def deleteProperty(self, name):
        prop = property.property(self, name)
        if prop:
            prop.delete()

    def getProperties(self):
        properties = db.Property.query(db.Property.id == self.id).fetch(1000)
        return properties

    def getTrustRelationships(self, relationship='', peerid='', type=''):
        if len(relationship) > 0 and len(peerid) > 0 and len(type) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.relationship == relationship and db.Trust.peerid == peerid and db.Trust.type == type).fetch(1000)
        elif len(peerid) > 0 and len(type) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.peerid == peerid and db.Trust.type == type).fetch(1000)
        elif len(relationship) > 0 and len(peerid) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.relationship == relationship and db.Trust.peerid == peerid).fetch(1000)
        elif len(relationship) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.relationship == relationship).fetch(1000)
        elif len(peerid) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.peerid == peerid).fetch(1000)
        elif len(type) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.type == type).fetch(1000)
        else:
            relationships = db.Trust.query(db.Trust.id == self.id).fetch(1000)
        return relationships

    def setTrustee(self, trustee):
        actor_query = db.Actor.query(db.Actor.id == self.id).get()
        if result:
            result.trustee = trustee
            result.put()

    # Returns False or new trust object if successful
    def createTrust(self, url, secret=None, desc='', rel='', type=''):
        if len(url) == 0:
            return False
        if not secret:
            return False
        Config = config.config()

        peer = getPeerInfo(url)
        if self.last_response_code < 200 or self.last_response_code >= 300:
            return False
        if not peer.id or not peer.type or len(peer.type) == 0:
            logging.info("Received invalid peer info when trying to establish trust: " + url)
            return False
        if len(type) > 0:
            if type.lower() != peer.type.lower():
                return False
        if not rel or len(rel) == 0:
            rel = Config.default_relationship
        params = {
            'baseuri': Config.root + self.id,
            'id': self.id,
            'type': Config.type,
            'secret': secret,
            'desc': desc,
            'notify': 'false',
        }
        url = url + '/trust/' + rel
        response = urlfetch.fetch(url=url,
                                  method=urlfetch.POST,
                                  payload=data,
                                  headers={'Content-Type': 'application/json', }
                                  )
        self.last_response_code = response.status_code
        self.last_response_message = response.content

        if self.last_response_code == 201 or self.last_response_code == 202:
            new_trust = trust.trust(id, peer.id)
            # Don't implement notify for now...
            new_trust.create(baseuri=url, secret=secret, type=type,
                             rel=rel, active=True, notify=False, desc=desc)
            return new_trust
        else:
            return False

    def __init__(self, id=''):
        self.get(id)
