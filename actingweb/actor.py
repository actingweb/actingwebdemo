from db import db
import datetime
import property
import config

__all__ = [
    'actor',
]


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
        actor = db.Actor(creator=self.creator,
                         passphrase=self.passphrase,
                         id=self.id,
                         trustee=trustee)
        actor.put()

    def delete(self):
        properties = self.getProperties()
        for prop in properties:
            # We should really delete individual properties through the method, but this is quicker
            prop.key.delete()
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

    def setTrustee(self, trustee):
        actor_query = db.Actor.query(db.Actor.id == self.id).get()
        if result:
            result.trustee = trustee
            result.put()

    def __init__(self, id=''):
        self.get(id)
