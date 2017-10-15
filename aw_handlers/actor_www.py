import webapp2
from actingweb import auth
from on_aw import on_aw_www_paths


class actor_www(webapp2.RequestHandler):

    def get(self, id, path):
        (myself, check) = auth.init_actingweb(appreq=self,
                                              id=id, path='www', subpath=path,
                                              config=self.app.registry.get('config'))
        if not myself or check.response["code"] != 200:
            return
        if not self.app.registry.get('config').ui:
            self.response.set_status(404, "Web interface is not enabled")
            return
        if not check.checkAuthorisation(path='www', subpath=path, method='GET'):
            self.response.set_status(403)
            return

        if not path or path == '':
            template_values = {
                'url': self.request.url,
                'id': id,
                'creator': myself.creator,
                'passphrase': myself.passphrase,
            }
            template = self.app.registry.get('template').get_template('aw-actor-www-root.html')
            self.response.write(template.render(template_values).encode('utf-8'))
            return

        if path == 'init':
            template_values = {
                'id': myself.id,
            }
            template = self.app.registry.get('template').get_template('aw-actor-www-init.html')
            self.response.write(template.render(template_values).encode('utf-8'))
            return
        if path == 'properties':
            properties = myself.getProperties()
            template_values = {
                'id': myself.id,
                'properties': properties,
            }
            template = self.app.registry.get('template').get_template('aw-actor-www-properties.html')
            self.response.write(template.render(template_values).encode('utf-8'))
            return
        if path == 'property':
            lookup = myself.getProperty(self.request.get('name'))
            if lookup.value:
                template_values = {
                    'id': myself.id,
                    'property': lookup.name,
                    'value': lookup.value,
                    'qual': '',
                }
            else:
                template_values = {
                    'id': myself.id,
                    'property': lookup.name,
                    'value': 'Not set',
                    'qual': 'no',
                }
            template = self.app.registry.get('template').get_template('aw-actor-www-property.html')
            self.response.write(template.render(template_values).encode('utf-8'))
            return
        if path == 'trust':
            relationships = myself.getTrustRelationships()
            if not relationships or len(relationships) == 0:
                self.response.set_status(404, 'Not found')
                return
            for t in relationships:
                t["approveuri"] = self.app.registry.get('config').root + myself.id + '/trust/' + t.relationship + '/' + t.peerid
            template_values = {
                'id': myself.id,
                'trusts': relationships,
            }
            template = self.app.registry.get('template').get_template('aw-actor-www-trust.html')
            self.response.write(template.render(template_values).encode('utf-8'))
            return
        output = on_aw_www_paths.on_www_paths(myself=myself, req=self, auth=check, path=path)
        if output:
            self.response.write(output)
        else:
            self.response.set_status(404, "Not found")
        return

