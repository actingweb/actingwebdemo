from db_gae import db_property

__all__ = [
    'property',
    'properties',
]


class property():
    """
        property is the main entity keeping a property
    """

    def get(self):
        """ Retrieves the property from the database """
        if not self.dbprop:
            return
        self.value = self.dbprop.get(actorId=self. actorId, name=self.name)
        return self.value

    def set(self, value):
        """ Sets a new value for this property """
        if not self.dbprop:
            return
        self.value = value
        return self.dbprop.set(actorId=self. actorId, name=self.name, value=value)

    def delete(self):
        """ Deletes the property in the database """
        if not self.dbprop:
            return
        if self.dbprop.delete():
            self.value = None
            self.dbprop = None
            return True
        else:
            return False

    def __init__(self,  actorId=None, name=None, value=None):
        """ A property must be initialised with actorId and name or
            name and value (to find an actor's property of a certain value)
        """
        self.dbprop = db_property.db_property()
        if not actorId and len(name) > 0 and value and len(value) > 0:
            self. actorId = self.dbprop.get_actorId_from_property(name=name,
                                                                   value=value)
            if not self. actorId:
                return
            self.name = name
            self.value = value
        self. actorId = actorId
        if name and len(name) > 0:
            self.name = name
            self.get()


class properties():
    """ Handles all properties of a specific actor_id
    
        Access the indvidual dbprops in .dbprops and the properties
        in .props as a dictionary
    """

    def delete(self):
        if not self.dbprops:
            return False
        self.dbprops.delete()
        return True

    def __init__(self,  actorId=None):
        """ Properties must always be initialised with an actorId """
        if not actorId:
            self.dbprops = None
            return False
        self.dbprops = db_property.db_property_list()
        properties = self.dbprops.fetch(actorId=actorId)
        self.props = {}
        if not properties:
            return
        for d in properties:
            self.props[d.name] = d.value

