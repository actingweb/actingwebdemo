__all__ = [
    'config',
]

import uuid, binascii, os
import logging

class config():

    def __init__(self):
        self.ui = True
        self.root = ""
        self.type = "urn:actingweb:actingweb.org:gae-demo"
        self.desc = "GAE Demo actor"
        self.version = "1.0"
        self.info = "http://actingweb.org/"
        self.wadl = ""
        self.aw_version = "0.9"
        self.aw_supported = ""
        self.aw_formats = ""
        self.logLevel = logging.INFO #Change to WARN for production, DEBUG for debugging, and INFO for normal testing

        self.oauth = {
            'client_id': "",
            'client_secret': "",
            'redirect_uri': "",
            'scope': "",
            'auth_uri': "",
            'token_uri': "h",
        }

    def newUUID(self, seed):
        return uuid.uuid5(uuid.NAMESPACE_URL, seed).get_hex()

    def newToken(self, length = 40):
        return binascii.hexlify(os.urandom(int(length//2)))
