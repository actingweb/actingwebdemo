import webapp2
import json
from actingweb import auth

class actor_meta(webapp2.RequestHandler):

    def get(self, id, path):
        (myself, check) = auth.init_actingweb(appreq=self,
                                              id=id, path='meta',
                                              subpath=path,
                                              add_response=False,
                                              config=self.app.registry.get('config'))
        # We accept no auth here, so don't check response code
        if not myself:
            return
        if not check.checkAuthorisation(path='meta', subpath=path, method='GET'):
            self.response.set_status(403)
            return

        trustee_root = myself.getProperty('trustee_root').value
        if not trustee_root:
            trustee_root = ''
        if not path:
            values = {
                'id': id,
                'type': self.app.registry.get('config').type,
                'version': self.app.registry.get('config').version,
                'desc': self.app.registry.get('config').desc,
                'info': self.app.registry.get('config').info,
                'trustee_root': trustee_root,
                'specification': self.app.registry.get('config').specification,
                'aw_version': self.app.registry.get('config').aw_version,
                'aw_supported': self.app.registry.get('config').aw_supported,
                'aw_formats': self.app.registry.get('config').aw_formats,
            }
            out = json.dumps(values)
            self.response.write(out.encode('utf-8'))
            self.response.headers["Content-Type"] = "application/json"
            return

        elif path == 'id':
            out = id
        elif path == 'type':
            out = self.app.registry.get('config').type
        elif path == 'version':
            out = self.app.registry.get('config').version
        elif path == 'desc':
            out = self.app.registry.get('config').desc + myself.id
        elif path == 'info':
            out = self.app.registry.get('config').info
        elif path == 'trustee_root':
            out = trustee_root
        elif path == 'specification':
            out = self.app.registry.get('config').specification
        elif path == 'actingweb/version':
            out = self.app.registry.get('config').aw_version
        elif path == 'actingweb/supported':
            out = self.app.registry.get('config').aw_supported
        elif path == 'actingweb/formats':
            out = self.app.registry.get('config').aw_formats
        else:
            self.response.set_status(404)
            return
        self.response.write(out.encode('utf-8'))
