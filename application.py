import os
import sys
import json
import logging
from urllib.parse import urlparse
from flask import Flask, request, redirect, Response, render_template
from actingweb import config, aw_web_request, actor
import on_aw
from actingweb.handlers import callbacks, properties, meta, root, trust, devtest, \
    subscription, resources, oauth, callback_oauth, bot, www, factory
# To debug in pycharm inside the Docker container, remember to uncomment import pydevd as well
# (and add to requirements.txt)
#import pydevd_pycharm

logging.basicConfig(stream=sys.stderr, level=os.getenv('LOG_LEVEL', "INFO"))
LOG = logging.getLogger()
LOG.setLevel(os.getenv('LOG_LEVEL', "INFO"))

# Prefix url_path here with path if app is deployed in non-root URL
app = Flask(__name__, static_url_path='/static')

# The on_aw object we will use to do app-specific processing
OBJ_ON_AW = on_aw.OnAWDemo()


def get_config():
    # Having settrace here will make sure the process reconnects to the debug server on each request
    # which makes it easier to keep in sync when doing code changes
    # This is for pycharm
    #pydevd_pycharm.settrace('docker.for.mac.localhost', port=3001, stdoutToServer=True, stderrToServer=True,
    #                        suspend=False)
    #
    # The greger.ngrok.io address will be overriden by env variables from serverless.yml
    myurl = os.getenv('APP_HOST_FQDN', "greger.ngrok.io")
    proto = os.getenv('APP_HOST_PROTOCOL', "https://")
    # Replace with your URN here
    aw_type = "urn:actingweb:actingweb.org:actingwebdemo"
    bot_token = os.getenv('APP_BOT_TOKEN', "")
    bot_email = os.getenv('APP_BOT_EMAIL', "")
    bot_secret = os.getenv('APP_BOT_SECRET', "")
    bot_admin_room = os.getenv('APP_BOT_ADMIN_ROOM', "")
    oauth = {
        'client_id': os.getenv('APP_OAUTH_ID', ""),
        'client_secret': os.getenv('APP_OAUTH_KEY', ""),
        'redirect_uri': proto + myurl + "/oauth",
        'scope': "",
        'auth_uri': "https://api.actingweb.net/v1/authorize",
        'token_uri': "https://api.actingweb.net/v1/access_token",
        'response_type': "code",
        'grant_type': "authorization_code",
        'refresh_type': "refresh_token",
        # Example oauth_extras for google
        #'oauth_extras': {
        #    'access_type': 'offline',
        #    'include_granted_scopes': 'false',
        #    'login_hint': 'dynamic:creator',
        #    'prompt': 'consent'
        #}
    }
    actors = {
        'myself': {
            'type': aw_type,
            'factory': proto + myurl + '/',
            'relationship': 'friend',  # associate, friend, partner, admin
        }
    }
    return config.Config(
        database='dynamodb',
        fqdn=myurl,
        proto=proto,
        aw_type=aw_type,
        desc="Actingwebdemo actor: ",
        version="2.3",
        devtest=True,
        actors=actors,
        force_email_prop_as_creator=False,
        unique_creator=False,
	    # Use "oauth" here if authenticating against a service
        www_auth="basic",
        logLevel=os.getenv('LOG_LEVEL', "INFO"),
        ui=True,
        bot={
            "token": bot_token,
            "email": bot_email,
            "secret": bot_secret,
            "admin_room": bot_admin_room
        },
        oauth=oauth
    )


class SimplifyRequest:

    def __init__(self, req):
        if isinstance(req, dict):
            self._req = req
            if isinstance(self._req['data'], str):
                req['data'] = req['data'].encode('utf-8')
            if 'method' not in self._req:
                self._req['method'] = 'POST'
            if 'path' not in req:
                self._req['path'] = urlparse(req['url']).path
        else:
            cookies = {}
            raw_cookies = req.headers.get("Cookie")
            if raw_cookies:
                for cookie in raw_cookies.split("; "):
                    name, value = cookie.split("=")
                    cookies[name] = value
            headers = {}
            for k, v in req.headers.items():
                headers[k] = v
            params = {}
            for k, v in req.values.items():
                params[k] = v
            self._req = {
                'method': req.method,
                'path': req.path,
                'data': req.data,
                'headers': headers,
                'cookies': cookies,
                'values': params,
                'url': req.url
            }

    def __getattr__(self, key):
        try:
            return self._req[key]
        except KeyError:
            raise AttributeError(key)


class Handler:

    def __init__(self, req):
        req = SimplifyRequest(req)
        self.handler = None
        self.response = None
        self.actor_id = None
        self.path = req.path
        self.method = req.method
        LOG.debug('Path: ' + req.url + ', params(' + json.dumps(req.values) + ')' + ', body (' +
                  json.dumps(req.data.decode('utf-8')) + ')')
        self.webobj = aw_web_request.AWWebObj(
            url=req.url,
            params=req.values,
            body=req.data,
            headers=req.headers,
            cookies=req.cookies
        )
        if not req or not self.path:
            return
        if self.path == '/':
            self.handler = factory.RootFactoryHandler(
                self.webobj, get_config(), on_aw=OBJ_ON_AW)
        else:
            path = self.path.split('/')
            self.path = path
            f = path[1]
            if f == 'oauth':
                self.handler = callback_oauth.CallbackOauthHandler(
                    self.webobj, get_config(), on_aw=OBJ_ON_AW)
            elif f == 'bot':
                self.handler = bot.BotHandler(
                    webobj=self.webobj, config=get_config(), on_aw=OBJ_ON_AW)
            elif len(path) == 2:
                self.handler = root.RootHandler(
                    self.webobj, get_config(), on_aw=OBJ_ON_AW)
            else:
                self.actor_id = f
                f = path[2]
                if f == 'meta':
                    # r'/<actor_id>/meta<:/?><path:(.*)>'
                    self.handler = meta.MetaHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'oauth':
                    # r'/<actor_id>/oauth<:/?><path:.*>'
                    self.handler = oauth.OauthHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'www':
                    # r'/<actor_id>/www<:/?><path:(.*)>'
                    self.handler = www.WwwHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'properties':
                    # r'/<actor_id>/properties<:/?><name:(.*)>'
                    self.handler = properties.PropertiesHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'trust':
                    # r'/<actor_id>/trust<:/?>'
                    # r'/<actor_id>/trust/<relationship><:/?>'
                    # r'/<actor_id>/trust/<relationship>/<peerid><:/?>'
                    if len(path) == 3:
                        self.handler = trust.TrustHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                    elif len(path) == 4:
                        self.handler = trust.TrustRelationshipHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                    elif len(path) >= 5:
                        self.handler = trust.TrustPeerHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'subscriptions':
                    # r'/<actor_id>/subscriptions<:/?>'
                    # r'/<actor_id>/subscriptions/<peerid><:/?>'
                    # r'/<actor_id>/subscriptions/<peerid>/<subid><:/?>'
                    # r'/<actor_id>/subscriptions/<peerid>/<subid>/<seqnr><:/?>'
                    if len(path) == 3:
                        self.handler = subscription.SubscriptionRootHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                    elif len(path) == 4:
                        self.handler = subscription.SubscriptionRelationshipHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                    elif len(path) == 5:
                        self.handler = subscription.SubscriptionHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                    elif len(path) >= 6:
                        self.handler = subscription.SubscriptionDiffHandler(
                            self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'callbacks':
                    # r'/<actor_id>/callbacks<:/?><name:(.*)>'
                    self.handler = callbacks.CallbacksHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'resources':
                    # r'/<actor_id>/resources<:/?><name:(.*)>'
                    self.handler = resources.ResourcesHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
                elif f == 'devtest':
                    # r'/<actor_id>/devtest<:/?><path:(.*)>'
                    self.handler = devtest.DevtestHandler(
                        self.webobj, get_config(), on_aw=OBJ_ON_AW)
        if not self.handler:
            LOG.warning('Handler was not set with path: ' + req.url)

    def process(self, **kwargs):
        try:
            if self.method == 'POST':
                self.handler.post(**kwargs)
            elif self.method == 'GET':
                self.handler.get(**kwargs)
            elif self.method == 'DELETE':
                self.handler.delete(**kwargs)
            elif self.method == 'PUT':
                self.handler.put(**kwargs)
        except AttributeError:
            return False
        if self.get_status() == 404:
            return False
        return True

    def get_redirect(self):
        if self.webobj.response.redirect:
            return self.get_response()
        return None

    def get_response(self):
        if self.webobj.response.redirect:
            self.response = redirect(self.webobj.response.redirect, code=302)
        else:
            if self.webobj.response.status_code == 401:
                # For this demo, you may have tested with different users, so
                # force a new domain, so that the browser will pop up the login window
                self.webobj.response.headers['WWW-Authenticate'] = 'Basic realm="' + self.actor_id +'"'
            self.response = Response(
                response=self.webobj.response.body,
                status=self.webobj.response.status_message,
                headers=self.webobj.response.headers
            )
        self.response.status_code = self.webobj.response.status_code
        if len(self.webobj.response.cookies) > 0:
            for a in self.webobj.response.cookies:
                self.response.set_cookie(a["name"], a["value"], max_age=a["max_age"], secure=a["secure"])
        return self.response

    def get_status(self):
        return self.webobj.response.status_code


@app.route('/', methods=['GET', 'POST'])
def app_root():
    h = Handler(request)
    if not h.process():
        return Response(status=404)
    if h.get_status() == 400:
        existing = actor.Actor(config=get_config())
        existing.get_from_creator(request.values.get('creator'))
        if existing.id:
            return redirect(get_config().root + existing.id + '/www?refresh=true', 302)
        else:
            return render_template('aw-root-failed.html', **h.webobj.response.template_values)
    if request.method == 'GET':
        return render_template('aw-root-factory.html', **h.webobj.response.template_values)
    if request.method == 'POST' and h.get_status() == 200:
        return render_template('aw-root-created.html', **h.webobj.response.template_values)
    return h.get_response()


@app.route('/<actor_id>', methods=['GET', 'POST', 'DELETE'], strict_slashes=False)
def app_actor_root(actor_id):
    h = Handler(request)
    if not h.process(actor_id=actor_id):
        return Response(status=404)
    return h.get_response()


@app.route('/<actor_id>/meta', methods=['GET'], strict_slashes=False)
@app.route('/<actor_id>/meta/<path:path>', methods=['GET'], strict_slashes=False)
def app_meta(actor_id, path=''):
    h = Handler(request)
    if not h.process(actor_id=actor_id, path=path):
        return Response(status=404)
    return h.get_response()


@app.route('/<actor_id>/oauth', methods=['GET'], strict_slashes=False)
@app.route('/<actor_id>/oauth/<path:path>', methods=['GET'], strict_slashes=False)
def app_oauth(actor_id, path=''):
    h = Handler(request)
    if not h.process(actor_id=actor_id, path=path):
        return Response(status=404)
    return h.get_response()


@app.route('/<actor_id>/www', methods=['GET', 'POST', 'DELETE'], strict_slashes=False)
@app.route('/<actor_id>/www/<path:path>', methods=['GET', 'POST', 'DELETE'], strict_slashes=False)
def app_www(actor_id, path=''):
    h = Handler(request)
    if not h.process(actor_id=actor_id, path=path):
        return Response(status=404)
    if h.get_redirect():
        return h.get_redirect()
    if h.webobj.response.status_code == 403:
        return Response(status=403)
    if request.method == 'GET' and h.get_status() == 200:
        if not path or path == '':
            return render_template('aw-actor-www-root.html', **h.webobj.response.template_values)
        elif path == 'init':
            return render_template('aw-actor-www-init.html', **h.webobj.response.template_values)
        elif path == 'properties':
            return render_template('aw-actor-www-properties.html', **h.webobj.response.template_values)
        elif path == 'property':
            return render_template('aw-actor-www-property.html', **h.webobj.response.template_values)
        elif path == 'trust':
            return render_template('aw-actor-www-trust.html', **h.webobj.response.template_values)
    return h.get_response()


@app.route('/<actor_id>/properties', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
@app.route('/<actor_id>/properties/<path:name>', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
def app_properties(actor_id, name=''):
    h = Handler(request)
    if not h.process(actor_id=actor_id, name=name):
        return Response(status=404)
    return h.get_response()


@app.route('/<actor_id>/trust', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
@app.route('/<actor_id>/trust/<relationship>', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
@app.route('/<actor_id>/trust/<relationship>/<peerid>', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
def app_trust(actor_id, relationship=None, peerid=None):
    h = Handler(request)
    if peerid:
        if not h.process(actor_id=actor_id, relationship=relationship, peerid=peerid):
            return Response(status=404)
    elif relationship:
        if not h.process(actor_id=actor_id, relationship=relationship):
            return Response(status=404)
    else:
        if not h.process(actor_id=actor_id):
            return Response(status=404)
    return h.get_response()


@app.route('/<actor_id>/subscriptions', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
@app.route('/<actor_id>/subscriptions/<peerid>', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
@app.route('/<actor_id>/subscriptions/<peerid>/<subid>', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
@app.route('/<actor_id>/subscriptions/<peerid>/<subid>/<int:seqnr>', methods=['GET'], strict_slashes=False)
def app_subscriptions(actor_id, peerid=None, subid=None, seqnr=None):
    h = Handler(request)
    if seqnr:
        if not h.process(actor_id=actor_id, peerid=peerid, subid=subid, seqnr=seqnr):
            return Response(status=404)
    elif subid:
        if not h.process(actor_id=actor_id, peerid=peerid, subid=subid):
            return Response(status=404)
    elif peerid:
        if not h.process(actor_id=actor_id, peerid=peerid):
            return Response(status=404)
    else:
        if not h.process(actor_id=actor_id):
            return Response(status=404)
    return h.get_response()


@app.route('/<actor_id>/resources', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
@app.route('/<actor_id>/resources/<path:name>', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
def app_resources(actor_id, name=''):
    h = Handler(request)
    if not h.process(actor_id=actor_id, name=name):
        return Response(status=404)
    return h.get_response()


@app.route('/<actor_id>/callbacks', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
@app.route('/<actor_id>/callbacks/<path:name>', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
def app_callbacks(actor_id, name=''):
    h = Handler(request)
    if not h.process(actor_id=actor_id, name=name):
        return Response(status=404)
    return h.get_response()


@app.route('/<actor_id>/devtest', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
@app.route('/<actor_id>/devtest/<path:path>', methods=['GET', 'POST', 'DELETE', 'PUT'], strict_slashes=False)
def app_devtest(actor_id, path=''):
    h = Handler(request)
    if not h.process(actor_id=actor_id, path=path):
        return Response(status=404)
    return h.get_response()


@app.route('/bot', methods=['POST'], strict_slashes=False)
def app_bot():
    h = Handler(request)
    if not h.process(path='/bot'):
        return Response(status=404)
    return h.get_response()


@app.route('/oauth', methods=['GET'], strict_slashes=False)
def app_oauth_callback():
    h = Handler(request)
    if not h.process():
        return Response(status=404)
    return h.get_response()


# Here is how you can add a google verification
#@app.route('/google123456.html', methods=['GET'], strict_slashes=False)
#def app_google_verify():
#    return Response("google-site-verification: google123456.html")
if __name__ == "__main__":
    logging.debug('Starting up the ActingWeb Demo ...')
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=5000)
