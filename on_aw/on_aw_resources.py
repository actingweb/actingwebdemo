__all__ = [
    'on_post_resources',
    'on_put_resources',
    'on_get_resources',
    'on_delete_resources',
]


def on_get_resources(myself, req, auth, name):
    """ Called on GET to resources. Return struct for json out.

        Returning {} will give a 404 response back to requestor. 
    """
    return {}


def on_delete_resources(myself, req, auth, name):
    """ Called on DELETE to resources. Return struct for json out.

        Returning {} will give a 404 response back to requestor. 
    """
    return {}


def on_put_resources(myself, req, auth, name, params):
    """ Called on PUT to resources. Return struct for json out.

        Returning {} will give a 404 response back to requestor. 
        Returning an error code after setting the response will not change
        the error code.
    """
    return {}


def on_post_resources(myself, req, auth, name, params):
    """ Called on POST to resources. Return struct for json out.

        Returning {} will give a 404 response back to requestor. 
        Returning an error code after setting the response will not change
        the error code.
    """
    return {}


