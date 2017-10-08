from flask import Flask

# EB looks for an 'application' callable by default.
application = Flask(__name__)

@application.route('/')
def welcome():
    return 'Hello World!'


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run(host='0.0.0.0')



    def post(self):
        myself = actor.actor()
        try:
            params = json.loads(self.request.body.decode('utf-8', 'ignore'))
            is_json = True
            if 'creator' in params:
                creator = params['creator']
            else:
                creator = ''
            if 'trustee_root' in params:
                trustee_root = params['trustee_root']
            else:
                trustee_root = ''
            if 'passphrase' in params:
                passphrase = params['passphrase']
            else:
                passphrase = ''
        except ValueError:
            is_json = False
            creator = self.request.get('creator')
            trustee_root = self.request.get('trustee_root')
            passphrase = self.request.get('passphrase')
        if not myself.create(url=self.request.url, creator=creator, passphrase=passphrase):
            self.response.set_status(400, 'Not created')
            logging.warn("Was not able to create new actor("+str(self.request.url) + " " +
                         str(creator) + ")")
            return
        if len(trustee_root) > 0:
            myself.setProperty('trustee_root', trustee_root)
        self.response.headers.add_header("Location", str(Config.root + myself.id))
        if Config.www_auth == 'oauth' and not is_json:
            self.redirect(Config.root + myself.id + '/www')
            return
        pair = {
            'id': myself.id,
            'creator': myself.creator,
            'passphrase': myself.passphrase,
        }
        if len(trustee_root) > 0:
            pair['trustee_root'] = trustee_root
        if Config.ui and not is_json:
            template = Template_env.get_template('aw-root-created.html')
            self.response.write(template.render(pair).encode('utf-8'))
            return
        out = json.dumps(pair)
        self.response.write(out)
        self.response.headers["Content-Type"] = "application/json"
        self.response.set_status(201, 'Created')
