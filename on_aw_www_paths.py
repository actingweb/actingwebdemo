#!/usr/bin/env python
#
from actingweb import actor
from actingweb import auth
from actingweb import config

import logging

import os
from google.appengine.ext.webapp import template

__all__ = [
    'on_www_paths',
]


def on_www_paths(path='', auth=None, myself=None):
    # THIS METHOD IS CALLED WHEN AN actorid/www/* PATH IS CALLED (AND AFTER ACTINGWEB DEFAULT PATHS HAVE BEEN HANDLED)
    # THE BELOW IS SAMPLE CODE
    # if path == '' or not auth or not myself:
    #    logging.info('Got an on_www_paths without proper parameters')
    #    return False
    #oauth=auth.oauth(token = myself.getProperty('oauth_token').value)
    # if path == 'something':
    #    return True
    # END OF SAMPLE CODE
    return False
