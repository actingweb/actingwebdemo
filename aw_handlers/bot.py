from actingweb import auth
from actingweb import config
from on_aw import on_aw_bot
import webapp2


class bot(webapp2.RequestHandler):

    def post(self, path):
        """Handles POST callbacks for bots."""

        if not self.app.registry.get('config').bot['token'] or \
                        len(self.app.registry.get('config').bot['token']) == 0:
            self.response.set_status(404)
            return
        check = auth.auth(id=None, config=self.app.registry.get('config'))
        check.oauth.token = self.app.registry.get('config').bot['token']
        ret = on_aw_bot.on_bot_post(req=self, auth=check, path=path)
        if ret and 100 <= ret < 999:
            self.response.set_status(ret)
            return
        elif ret:
            self.response.set_status(204)
            return
        else:
            self.response.set_status(404)
            return
