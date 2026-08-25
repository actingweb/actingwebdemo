# OAuth2 Setup (Google or GitHub)

This app authenticates users via OAuth2 — Google or GitHub — and creates one
ActingWeb actor per user, identified by their email (or, for GitHub users
with no public email, `username@github.local`). This guide covers setting
up credentials with either provider for this deployment specifically.

For how the ActingWeb library's OAuth2 login flow works in general —
factory-page login buttons, actor creation deferred until after the email is
known, the underlying protocol — see `docs/guides/authentication.rst` and
`docs/guides/spa-authentication.rst` in the `actingweb` library repo.

## Choosing a provider

**Google** (default) — provides email and profile info, supports refresh
tokens, uses OpenID Connect.

**GitHub** — developer-friendly, provides username and (if public) email;
handles private email gracefully by falling back to
`username@github.local`; no refresh tokens, so users re-authenticate when a
token expires.

## Step 1: Register an OAuth2 app with your provider

### Google

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and
   create (or select) a project.
2. Under APIs & Services > Credentials, create an **OAuth 2.0 Client ID**:
   - Application type: Web application
   - Authorized redirect URI: `https://your-domain.com/oauth/callback` (add
     `https://your-ngrok-id.ngrok.io/oauth/callback` too if testing via
     ngrok)
3. You'll get a **Client ID** (`...apps.googleusercontent.com`) and
   **Client Secret** (`GOCSPX-...`).

### GitHub

1. Go to [GitHub Settings > Developer settings > OAuth
   Apps](https://github.com/settings/applications/new) and create a new
   OAuth App:
   - Homepage URL: `https://your-domain.com`
   - Authorization callback URL: `https://your-domain.com/oauth/callback`
     (or your ngrok URL, for local testing)
2. You'll get a **Client ID** (`Iv1....`) and, after generating one, a
   **Client Secret**.
3. GitHub OAuth apps request `user:email` and basic profile scope by
   default — no extra configuration needed.

## Step 2: Configure environment variables

Copy `vendor/actingweb/examples/demo/.env.example` to `.env` at this repo's
root (never commit it — it's gitignored) and fill in:

```bash
# Google
OAUTH_PROVIDER=google
OAUTH_CLIENT_ID=123456789-abcdef.apps.googleusercontent.com
OAUTH_CLIENT_SECRET=GOCSPX-your-secret-here

# or GitHub
OAUTH_PROVIDER=github
OAUTH_CLIENT_ID=Iv1.a1b2c3d4e5f6g7h8
OAUTH_CLIENT_SECRET=your-github-client-secret

# Required either way — OAuth2 redirect URIs are derived from these two
APP_HOST_FQDN=your-domain.com   # or your-ngrok-id.ngrok.io for local testing
APP_HOST_PROTOCOL=https://
```

For a Lambda deployment, `OAUTH_CLIENT_ID`/`OAUTH_CLIENT_SECRET` are passed
as GitHub repository secrets and `OAUTH_PROVIDER` as a repository variable —
see the "Deployment" section of [README.md](README.md).

### Local testing with ngrok

```bash
ngrok http 5000
```

Then set `APP_HOST_FQDN` to the ngrok hostname (e.g. `abc123.ngrok.io`) and
`APP_HOST_PROTOCOL=https://`, and add the ngrok callback URL to your OAuth
app's allowed redirect URIs.

## Step 3: Authentication flow

1. A user visits the app's factory page and clicks "Login with Google" (or
   GitHub).
2. They're redirected to the provider, sign in, and grant permission.
3. The provider redirects back to `/oauth/callback` with an authorization
   code.
4. The app exchanges the code for a token, looks up the user's email (or
   GitHub username, if email is private), and either finds their existing
   actor or creates a new one.
5. The user lands on their actor's dashboard at `/{actor_id}/www`.

Every request is validated against the provider on each use of the
resulting session — an expired or revoked token fails validation rather than
being trusted indefinitely.

## Actor identity and isolation

- Google user `alice@gmail.com` and GitHub user `alice` are different
  actors — email/username plus provider together determine identity.
- Each actor's properties are completely isolated; there is no cross-actor
  data access.
- `OAUTH_PROVIDER` is a single deployment-wide setting: a running instance
  of this app supports one provider at a time, not both simultaneously.

## Troubleshooting

**"OAuth2 not configured"** — check `OAUTH_CLIENT_ID` and
`OAUTH_CLIENT_SECRET` are set, and `OAUTH_PROVIDER` is `google` or `github`.

**"Redirect URI mismatch"** — the callback URL registered with the provider
must exactly match `{APP_HOST_PROTOCOL}{APP_HOST_FQDN}/oauth/callback`.

**"Token validation failed"** — for GitHub, tokens have no refresh path, so
an expired token means re-authenticating; for Google, confirm the OAuth
consent screen and scopes are configured correctly in Cloud Console.

**"Actor creation failed"** — check DynamoDB connectivity
(`AWS_DB_HOST`/`AWS_DB_PREFIX` for local runs) and look for a unique-creator
constraint conflict.

**GitHub email not found** — GitHub users with a private email fall back to
`username@github.local` automatically; this is expected, not an error.

Enable verbose logging with `LOG_LEVEL=DEBUG` to see authentication attempts,
token validation, and actor lookup/creation in the logs.
