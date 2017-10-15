__all__ = [
    'on_www_paths',
]


def on_www_paths(myself, req, auth, path=''):
    # THIS METHOD IS CALLED WHEN AN actorid/www/* PATH IS CALLED (AND AFTER ACTINGWEB DEFAULT PATHS HAVE BEEN HANDLED)
    # THE BELOW IS SAMPLE CODE
    # if path == '' or not myself:
    #    logging.info('Got an on_www_paths without proper parameters.')
    #    return False
    # if path == 'something':
    #    return True
    # END OF SAMPLE CODE
    return False
