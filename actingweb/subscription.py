import actor
from db import db
import config
import datetime

__all__ = [
    'subscription',
]


class subscription():

    def get(self):
        if self.peerid and self.subid:
            result = db.Subscription.query(db.Subscription.id == self.actor.id,
                                           db.Subscription.peerid == self.peerid,
                                           db.Subscription.subid == self.subid).get()
            if result:
                self.subscription = result
                self.target = result.target
                self.subtarget = result.subtarget
                self.granularity = result.granularity

    def create(self, target=None, subtarget=None, granularity=None):
        Config = config.config()
        if not self.peerid:
            return False
        if not target:
            target = ''
        if not subtarget:
            subtarget = ''
        if not granularity:
            granularity = ''
        self.target = target
        self.subtarget = subtarget
        self.granularity = granularity
        if not self.subid:
            now = datetime.datetime.now()
            seed = Config.root + now.strftime("%Y%m%dT%H%M%S")
            self.subid = Config.newUUID(seed)
        elif self.subid and self.peerid and not self.subscription:
            self.get()
        if self.subscription:
            self.subscription.target = target
            self.subscription.subtarget = subtarget
            self.subscription.granularity = granularity
        else:
            self.subscription = db.Subscription(id=self.actor.id,
                                                peerid=self.peerid,
                                                subid=self.subid,
                                                target=target,
                                                subtarget=subtarget,
                                                granularity=granularity
                                                )
        self.subscription.put()
        return True

    def delete(self):
        if self.subscription:
            self.subscription.key.delete()
            return True
        return False

    def __init__(self, actor=None, peerid=None, subid=None):
        if not actor:
            return False
        self.actor = actor
        self.peerid = peerid
        self.subid = subid
        self.subscription = None
        if self.actor.id and self.peerid and self.subid:
            self.get()
