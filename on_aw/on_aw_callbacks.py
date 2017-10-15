import logging
import json

__all__ = [
    'on_post_callbacks',
    'on_get_callbacks',
    'on_post_subscriptions',
    'on_delete_callbacks',
]


def on_get_callbacks(myself, req, auth, name):
    """Customizible function to handle GET /callbacks"""
    # return True if callback has been processed
    # THE BELOW IS SAMPLE CODE
    #my_oauth=oauth.oauth(token = myself.getProperty('oauth_token').value)
    # if name == 'something':
    #    return
    # END OF SAMPLE CODE
    return False


def on_delete_callbacks(myself, req, auth, name):
    """Customizible function to handle DELETE /callbacks"""
    # return True if callback has been processed
    return False


def on_post_callbacks(myself, req, auth, name):
    """Customizible function to handle POST /callbacks"""
    # return True if callback has been processed
    # THE BELOW IS SAMPLE CODE
    #Config = config.config()
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
    return False


def on_post_subscriptions(myself, req, auth, sub, peerid, data):
    """Customizible function to process incoming callbacks/subscriptions/ callback with json body, return True if processed, False if not."""
    logging.debug("Got callback and processed " + sub["subscriptionid"] +
                  " subscription from peer " + peerid + " with json blob: " + json.dumps(data))
    return True
