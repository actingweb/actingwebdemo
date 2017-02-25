from google.appengine.ext import ndb

"""
    db_actor handles all db operations for an actor
    Google datastore for google is used as a backend.
"""

__all__ = [
    'db_actor',
]


class Actor(ndb.Model):
    """
       NDB data model for an actor
    """
    id = ndb.StringProperty(required=True)
    creator = ndb.StringProperty()
    passphrase = ndb.StringProperty()


class db_actor():
    """
        db_actor does all the db operations for actor objects

    """

    def get(self,  actorId=None):
        """ Retrieves the actor from the database """
        if not actorId:
            return None
        self.handle = Actor.query(Actor.id == actorId).get(use_cache=False)
        if self.handle:
            t = self.handle
            return {
                "id": t.id,
                "creator": t.creator,
                "passphrase": t.passphrase,
            }
        else:
            return None

    def modify(self, creator=None,
               passphrase=None):
        """ Modify an actor """
        if not self.handle:
            logging.debug("Attempted modification of db_actor without db handle")
            return False
        if creator and len(creator) > 0:
            self.handle.creator = creator
        if passphrase and len(passphrase) > 0:
            self.handle.passphrase = passphrase
        self.handle.put(use_cache=False)
        return True

    def create(self, actorId=None, creator=None,
               passphrase=None):
        """ Create a new actor """
        if not actorId:
            return False
        if not creator:
            creator = ''
        if not passphrase:
            passphrase = ''
        self.handle = Actor(id=actorId,
                            creator=creator,
                            passphrase=passphrase)
        self.handle.put(use_cache=False)
        return True

    def delete(self):
        """ Deletes the actor in the database """
        if not self.handle:
            logging.debug("Attempted delete of db_actor without db handle")
            return False
        self.handle.key.delete(use_cache=False)
        self.handle = None
        return True

    def __init__(self):
        self.handle = None

