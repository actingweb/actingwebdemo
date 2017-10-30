import webapp2


class callback_oauth(webapp2.RequestHandler):

    def get(self):
        if not self.request.get('code'):
            self.response.set_status(400, "Bad request. No code.")
            return
        code = self.request.get('code')
        id = self.request.get('state')
        Config = self.app.registry.get('config')
        self.redirect(Config.root + str(id) + '/oauth?code=' + str(code))

