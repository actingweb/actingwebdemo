from db import db
import datetime
import time
import property
import urllib
from google.appengine.api import urlfetch
import json
import config
import trust
import subscription
import logging

__all__ = [
    'actor',
]


def getPeerInfo(url):
    """Contacts an another actor over http/s to retrieve meta information."""
    try:
        response = urlfetch.fetch(url=url + '/meta',
                                  method=urlfetch.GET
                                  )
        res = {
            "last_response_code": response.status_code,
            "last_response_message": response.content,
            "data": json.loads(response.content),
        }
    except:
        res = {
            "last_response_code": 500,
        }
    return res


class actor():

    def get(self, id):
        """Retrieves an actor from db or initialises if does not exist."""
        result = db.Actor.query(db.Actor.id == id).get()
        if result:
            self.id = id
            self.creator = result.creator
            self.passphrase = result.passphrase
        else:
            self.id = None
            self.creator = None
            self.passphrase = None

    def create(self, url, creator, passphrase):
        """"Creates a new actor and persists it to db."""
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
        actor = db.Actor(creator=self.creator,
                         passphrase=self.passphrase,
                         id=self.id)
        actor.put()

    def delete(self):
        """Deletes an actor and cleans up all relevant stored data in db."""
        properties = db.Property.query(db.Property.id == self.id).fetch()
        for prop in properties:
            prop.key.delete()
        relationships = db.Trust.query(db.Trust.id == self.id).fetch()
        for rel in relationships:
            rel.key.delete()
        subs = db.Subscription.query(db.Subscription.id == self.id).fetch()
        for sub in subs:
            sub.key.delete()
        result = db.Actor.query(db.Actor.id == self.id).get()
        if result:
            result.key.delete()

    def setProperty(self, name, value):
        """Sets an actor's property name to value."""
        prop = property.property(self, name)
        prop.set(value)

    def getProperty(self, name):
        """Retrieves a property name."""
        prop = property.property(self, name)
        return prop

    def deleteProperty(self, name):
        """Deletes a property name."""
        prop = property.property(self, name)
        if prop:
            prop.delete()

    def getProperties(self):
        """Retrieves properties from db."""
        properties = db.Property.query(db.Property.id == self.id).fetch()
        return properties

    def getTrustRelationships(self, relationship='', peerid='', type=''):
        """Retrieves all trust relationships or filtered."""
        if len(relationship) > 0 and len(peerid) > 0 and len(type) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.relationship == relationship and db.Trust.peerid == peerid and db.Trust.type == type).fetch()
        elif len(peerid) > 0 and len(type) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.peerid == peerid and db.Trust.type == type).fetch()
        elif len(relationship) > 0 and len(peerid) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.relationship == relationship and db.Trust.peerid == peerid).fetch()
        elif len(relationship) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.relationship == relationship).fetch()
        elif len(peerid) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.peerid == peerid).fetch()
        elif len(type) > 0:
            relationships = db.Trust.query(
                db.Trust.id == self.id and db.Trust.type == type).fetch()
        else:
            relationships = db.Trust.query(db.Trust.id == self.id).fetch()
        rels = []
        for rel in relationships:
            rels.append(trust.trust(self.id, rel.peerid))
        return rels

    def modifyTrustAndNotify(self, relationship=None, peerid=None, baseuri='', secret='', desc='', approved=None, verified=None, verificationToken=None, peer_approved=None):
        """Changes a trust relationship and noties the peer if approval is changed."""
        if not relationship or not peerid:
            return False
        relationships = self.getTrustRelationships(
            relationship=relationship, peerid=peerid)
        if not relationships:
            return False
        trust = relationships[0]
        # If we change approval status, send the changed status to our peer
        if approved == True and trust.approved == False:
            params = {
                'approved': True,
            }
            requrl = trust.baseuri + '/trust/' + relationship + '/' + self.id
            if trust.secret:
                headers = {'Authorization': 'Bearer ' + trust.secret,
                           'Content-Type': 'application/json',
                           }
            data = json.dumps(params)
            # Note the POST here instead of PUT. POST is used to used to notify about
            # state change in the relationship (i.e. not change the object as PUT
            # would do)
            try:
                response = urlfetch.fetch(url=requrl,
                                          method=urlfetch.POST,
                                          payload=data,
                                          headers=headers
                                          )
                self.last_response_code = response.status_code
                self.last_response_message = response.content
            except:
                self.last_response_code = 500

        return relationships[0].modify(baseuri=baseuri, secret=secret, desc=desc, approved=approved, verified=verified, verificationToken=verificationToken, peer_approved=peer_approved)

        # Returns False or new trust object if successful
    def createReciprocalTrust(self, url, secret=None, desc='', relationship='', type=''):
        """Creates a new reciprocal trust relationship locally and by requesting a relationship from a peer actor."""
        if len(url) == 0:
            return False
        if not secret:
            return False
        Config = config.config()

        res = getPeerInfo(url)
        if not res or res["last_response_code"] < 200 or res["last_response_code"] >= 300:
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
        # Since we are initiating the relationship, we implicitly approve it
        # It is not verified until the peer has verified us
        new_trust.create(baseuri=url, secret=secret, type=peer["type"],
                         relationship=relationship, approved=True, verified=False, desc=desc)
        # Add a sleep here to make sure that appengine has time to write the new
        # relationship to datastore before we try to create the new trust with peer
        # time.sleep(0.4)
        params = {
            'baseuri': Config.root + self.id,
            'id': self.id,
            'type': Config.type,
            'secret': secret,
            'desc': desc,
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
            # Reload the trust to check if approval was done
            mod_trust = trust.trust(self.id, peer["id"])
            if not mod_trust.trust:
                logging.error("Couldn't find trust relationship after peer POST and verification")
                return False
            if self.last_response_code == 201:
                # Already approved by peer (probably auto-approved)
                # Do it direct on the trust (and not self.modifyTrustAndNotify) to avoid a callback
                # to the peer
                mod_trust.modify(peer_approved=True)
            return mod_trust
        else:
            new_trust.delete()
            return False

    def createVerifiedTrust(self, baseuri='', peerid=None, approved=False, secret=None, verificationToken=None, type=None, peer_approved=None, relationship=None, desc=''):
        """Creates a new trust when requested and call backs to initiating actor to verify relationship."""
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
        if not new_trust.create(baseuri=baseuri, secret=secret, type=type, approved=approved, peer_approved=peer_approved,
                                relationship=relationship, verified=verified, desc=desc):
            return False
        else:
            return new_trust

    def deleteReciprocalTrust(self, peerid=None, deletePeer=False):
        """Deletes a trust relationship and requests deletion of peer's relationship as well."""
        failedOnce = False  # For multiple relationships, this will be True if at least one deletion at peer failed
        successOnce = False  # True if at least one relationship was deleted at peer
        if not peerid:
            rels = self.getTrustRelationships()
        else:
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
                    failedOnce = True
                    continue
                else:
                    successOnce = True
            rel.trust.key.delete()
        if deletePeer and (not successOnce or failedOnce):
            return False
        return True

    def createSubscription(self, peerid=None, target=None, subtarget=None, granularity=None):
        new_sub = subscription.subscription(self, peerid)
        new_sub.create(target=target, subtarget=subtarget, granularity=granularity)
        return new_sub

    def getSubscriptions(self, peerid=None, target=None, subtarget=None):
        """Retrieves subscriptions from db."""
        if peerid and target and subtarget:
            subs = db.Subscription.query(
                db.Subscription.id == self.id and db.Subscription.peerid == peerid and db.Subscription.target == target and db.Subscription.subtarget == subtarget).fetch()
        elif peerid and target:
            subs = db.Subscription.query(
                db.Subscription.id == self.id and db.Subscription.peerid == peerid and db.Subscription.target == target).fetch()
        elif peerid:
            subs = db.Subscription.query(
                db.Subscription.id == self.id and db.Subscription.peerid == peerid).fetch()
        elif target and subtarget:
            subs = db.Subscription.query(
                db.Subscription.id == self.id and db.Subscription.target == target and db.Subscription.subtarget == subtarget).fetch()
        elif target:
            subs = db.Subscription.query(
                db.Subscription.id == self.id and db.Subscription.target == target).fetch()
        else:
            subs = db.Subscription.query(db.Subscription.id == self.id).fetch()
        return subs

    def __init__(self, id=''):
        self.get(id)
