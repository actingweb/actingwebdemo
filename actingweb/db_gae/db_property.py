from google.appengine.ext import ndb

"""
    db_property handles all db operations for a property
    Google datastore for google is used as a backend.
"""

__all__ = [
    'db_property',
    'db_property_list',
]


class Property(ndb.Model):
    """
       NDB data model for a property
    """
    id = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    value = ndb.TextProperty()


class db_property():
    """
        db_property does all the db operations for property objects

        The  actorId must always be set.
    """

    def get(self,  actorId, name):
        """ Retrieves the property from the database """
        if not actorId or not name:
            return None
        self.handle = Property.query(Property.id == actorId,
                                     Property.name == name).get(use_cache=False)
        if self.handle:
            return self.handle.value
        else:
            return None

    def get_actorId_from_property(self, name, value):
        """ Retrives an  actorId based on the value of a property.

        Note that this is a costly operation as all properties of this type
        must be retrieved and processed as value is TextProperty and cannot
        be indexed.
        """
        if not name or not value:
            return None
        results = Property.query(Property.name == name).fetch(use_cache=False)
        self.handle = None
        for res in results:
            if res.value != value:
                continue
            self.handle = res
            break
        if not self.handle:
            return None
        return self.handle.id

    def set(self,  actorId, name, value):
        """ Sets a new value for the property name """
        if not actorId or not name:
            return False
        if not self.handle:
            self.handle = Property.query(Property.id == actorId,
                                         Property.name == name).get(use_cache=False)
        if not self.handle:
            self.handle = Property(id=actorId, name=name,
                                   value=value)
        else:
            self.handle.value = value
        self.handle.put(use_cache=False)
        return True

    def delete(self):
        """ Deletes the property in the database """
        if not self.handle:
            return False
        self.handle.key.delete(use_cache=False)
        self.handle = None
        return True

    def __init__(self):
        self.handle = None


class db_property_list():
    """
        db_property does all the db operations for list of property objects

        The  actorId must always be set.
    """

    def fetch(self,  actorId):
        """ Retrieves the properties of an actorId from the database """
        if not actorId:
            return None
        self.handle = Property.query(Property.id == actorId).fetch(use_cache=False)
        if self.handle:
            return self.handle
        else:
            return None

    def delete(self):
        """ Deletes all the properties in the database """
        if not self.handle:
            return False
        for p in self.handle:
            p.key.delete(use_cache=False)
        self.handle = None
        return True

    def __init__(self):
        self.handle = None
