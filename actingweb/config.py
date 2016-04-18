__all__ = [
    'config',
]

import uuid
import binascii
import os
import logging


class config():

    def __init__(self):
        self.ui = True                                      # Turn on the /www path
        # Use basic auth  for /www path with creator and passphrase set/generated
        # when actor is created
        self.www_auth = "basic"
        # URI for this app's actor factory with slash at end
        self.root = "https://actingwebdemo.appspot.com/"
        self.type = "urn:actingweb:actingweb.org:gae-demo"  # The type of this actor
        # A human-readable description for this specific actor
        self.desc = "GAE Demo actor: "
        self.version = "1.0"                                # A version number for this app
        self.info = "http://actingweb.org/"                 # Where can more info be found
        self.aw_version = "0.9"                             # This app follows the actingweb specification specified
        self.aw_supported = ""                              # This app supports the following options
        self.aw_formats = "json"                            # These are the supported formats
        self.logLevel = logging.INFO  # Change to WARN for production, DEBUG for debugging, and INFO for normal testing
        # Hack to get access to GAE default logger
        logging.getLogger().handlers[0].setLevel(self.logLevel)

        self.auth_realm = "actingwebdemo.appspot.com"
        self.oauth = {
            'client_id': "",        # An empty client_id turns off oauth capabilities
            'client_secret': "",
            'redirect_uri': "",
            'scope': "",
            'auth_uri': "",
            'token_uri': "",
            'response_type': "code",
            'grant_type': "authorization_code",
            'refresh_type': "refresh_token",
        }

    def newUUID(self, seed):
        return uuid.uuid5(uuid.NAMESPACE_URL, seed).get_hex()

    def newToken(self, length=40):
        return binascii.hexlify(os.urandom(int(length // 2)))
