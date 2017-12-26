import webapp2
from actingweb import aw_web_request
from actingweb.handlers import callbacks
import on_aw


# noinspection PyAttributeOutsideInit
class ActorCallbacks(webapp2.RequestHandler):

    def init(self):
        self.obj = aw_web_request.AWWebObj(
            url=self.request.url,
            params=self.request.params,
            body=self.request.body,
            headers=self.request.headers)
        self.handler = callbacks.CallbacksHandler(self.obj, self.app.registry.get('config'), on_aw=on_aw.OnAWDemo())

    def get(self, actor_id, name):
        self.init()
        # Process the request
        self.handler.get(actor_id, name)
        # Pass results back to webapp2
        self.response.set_status(self.obj.response.status_code, self.obj.response.status_message)
        self.response.headers = self.obj.response.headers
        self.response.write(self.obj.response.body)

    def put(self, actor_id, name):
        self.init()
        # Process the request
        self.handler.put(actor_id, name)
        # Pass results back to webapp2
        self.response.set_status(self.obj.response.status_code, self.obj.response.status_message)
        self.response.headers = self.obj.response.headers
        self.response.write(self.obj.response.body)

    def delete(self, actor_id, name):
        self.init()
        # Process the request
        self.handler.delete(actor_id, name)
        # Pass results back to webapp2
        self.response.set_status(self.obj.response.status_code, self.obj.response.status_message)
        self.response.headers = self.obj.response.headers
        self.response.write(self.obj.response.body)

    def post(self, actor_id, name):
        self.init()
        # Process the request
        self.handler.post(actor_id, name)
        # Pass results back to webapp2
        self.response.set_status(self.obj.response.status_code, self.obj.response.status_message)
        self.response.headers = self.obj.response.headers
        self.response.write(self.obj.response.body)
