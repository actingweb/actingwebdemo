#!/usr/bin/env python
#
from actingweb import actor
from actingweb import oauth
from actingweb import config
from google.appengine.ext import deferred

import logging
import json
import os
import time
from google.appengine.ext.webapp import template


__all__ = [
    'on_post_callbacks',
    'on_get_callbacks',
]


def on_get_callbacks(myself, req, name):
    # THE BELOW IS SAMPLE CODE
    #my_oauth=oauth.oauth(token = myself.getProperty('oauth_token').value)
    # if name == 'something':
    #    return
    # END OF SAMPLE CODE
    return


def on_post_callbacks(myself, req, name):
    # THE BELOW IS SAMPLE CODE
    #Config = config.config()
    #my_oauth=oauth.oauth(token = myself.getProperty('oauth_token').value)
    #logging.debug("Callback body: "+req.request.body.decode('utf-8', 'ignore'))
    # non-json POSTs to be handled first
    # if name == 'somethingelse':
    #    return True
    # Handle json POSTs below
    #body = json.loads(req.request.body.decode('utf-8', 'ignore'))
    #data = body['data']
    # if name == 'somethingmore':
    #    callback_id = req.request.get('id')
    #    req.response.set_status(204)
    #    return True
    #req.response.set_status(403, "Callback not found.")
    # END OF SAMPLE CODE
    return True
