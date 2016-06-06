from db import db
import datetime
import property
import urllib
from google.appengine.api import urlfetch
import json
import config
import trust

__all__ = [
    'actor',
]


def getPeerInfo(url):
    response = urlfetch.fetch(url=url + '/meta',
                              method=urlfetch.GET
                              )
    try:
        res = {
            "last_response_code": response.status_code,
            "last_response_message": response.content,
            "data": json.loads(response.content),
        }
    except ValueError:
        res["last_response_code"] = 500
    return res


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
            rel.trust.key.delete()
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
        rels = []
        for rel in relationships:
            rels.append(trust.trust(self.id, rel.peerid))
        return rels

    def setTrustee(self, trustee):
        actor_query = db.Actor.query(db.Actor.id == self.id).get()
        if result:
            result.trustee = trustee
            result.put()

    # Returns False or new trust object if successful
    def createReciprocalTrust(self, url, secret=None, desc='', relationship='', type=''):
        if len(url) == 0:
            return False
        if not secret:
            return False
        Config = config.config()

        res = getPeerInfo(url)
        if res["last_response_code"] < 200 or res["last_response_code"] >= 300:
            return False
        peer = res["data"]
        if not peer["id"] or not peer["type"] or len(peer["type"]) == 0:
            logging.info("Received invalid peer info when trying to establish trust: " + url)
            return False
        if len(type) > 0:
            if type.lower() != peer["type"].lower():
                logging.info("Peer is of the wrong actingweb type: " + peer["type"])
                return False
        if not relationship or len(relationship) == 0:
            relationship = Config.default_relationship
        # Create trust, so that peer can do a verify on the relationship (using
        # verificationToken) when we request the relationship
        new_trust = trust.trust(self.id, peer["id"])
        # Don't implement notify for now...
        new_trust.create(baseuri=url, secret=secret, type=type,
                         relationship=relationship, active=False, notify=False, verified=False, desc=desc)
        params = {
            'baseuri': Config.root + self.id,
            'id': self.id,
            'type': Config.type,
            'secret': secret,
            'desc': desc,
            'notify': 'false',
            'verify': new_trust.verificationToken,
        }
        requrl = url + '/trust/' + relationship
        data = json.dumps(params)
        response = urlfetch.fetch(url=requrl,
                                  method=urlfetch.POST,
                                  payload=data,
                                  headers={'Content-Type': 'application/json', }
                                  )
        self.last_response_code = response.status_code
        self.last_response_message = response.content

        if self.last_response_code == 201 or self.last_response_code == 202:
            # Relead the trust to check if verification was done
            mod_trust = trust.trust(self.id, peer["id"])
            if not mod_trust.trust:
                logging.error("Couldn't find trust relationship after peer POST and verification")
                return False
            if mod_trust.verified:
                mod_trust.modify(active=True)
            return mod_trust
        else:
            new_trust.delete()
            return False

    def createVerifiedTrust(self, baseuri='', peerid=None, active=False, secret=None, verificationToken=None, type=None, relationship=None, notify=False, desc=''):
        if not peerid or len(baseuri) == 0 or not relationship:
            return False
        requrl = baseuri + '/trust/' + relationship + '/' + self.id
        headers = {}
        if secret:
            headers = {'Authorization': 'Bearer ' + secret,
                       }
        try:
            response = urlfetch.fetch(url=requrl,
                                      method=urlfetch.GET,
                                      headers=headers)
            self.last_response_code = response.status_code
            self.last_response_message = response.content
            try:
                data = json.loads(response.content)
                if data["verificationToken"] == verificationToken:
                    verified = True
                else:
                    verified = False
            except ValueError:
                verified = False
        except:
            verified = False
        new_trust = trust.trust(self.id, peerid)
        if not new_trust.create(baseuri=baseuri, secret=secret, type=type, active=active,
                                relationship=relationship, verified=verified, desc=desc):
            return False
        else:
            return new_trust

    def deleteReciprocalTrust(self, peerid=None, deletePeer=False):
        if not peerid:
            return False
        rels = self.getTrustRelationships(peerid=peerid)
        for rel in rels:
            if deletePeer:
                url = rel.baseuri + '/trust/' + rel.relationship + '/' + self.id
                headers = {}
                if rel.secret:
                    headers = {'Authorization': 'Bearer ' + rel.secret,
                               }
                response = urlfetch.fetch(url=url,
                                          method=urlfetch.DELETE,
                                          headers=headers)
                if (response.status_code < 200 or response.status_code > 299) and response.status_code != 404:
                    return False
            rel.trust.key.delete()
        return True

    def __init__(self, id=''):
        self.get(id)
