# actingwebdemo

The live reference deployment of the [ActingWeb](https://actingweb.org) REST
protocol, running at [demo.actingweb.io](https://demo.actingweb.io).

This repository is a thin deployment shell. **The application code itself
lives in the `actingweb` library repository**, at
[`examples/demo/`](https://github.com/actingweb/actingweb/tree/master/examples/demo).
This repo vendors that code as a git submodule (`vendor/actingweb`) and adds
what a library example doesn't need: AWS Lambda packaging (Serverless
Framework), a Docker/uWSGI setup, and the CI/CD pipeline that deploys to
`demo.actingweb.io`.

`application.py` at the repository root is a small WSGI shim: it loads
`vendor/actingweb/examples/demo/application.py` by file path and re-exports
`app`, so `uwsgi.ini` and `serverless.yml` have a stable entrypoint regardless
of where the real code lives. See the comments in `application.py` for why
it's loaded this way rather than imported normally.

## What the demo shows

The vendored app is a pure ActingWeb protocol demo — OAuth2 login, methods,
actions, callbacks, property hooks, trust, and subscriptions. It is **not**
an MCP (Model Context Protocol) integration example; the actingweb library
has a separate example for that (`examples/mcp_quickstart.py`).

It implements the four kinds of hooks the ActingWeb spec defines, plus
property and lifecycle hooks:

**Methods** — read-only RPC calls (`POST /{actor_id}/methods/{name}`)

- `calculate` — arithmetic on two numbers (add/subtract/multiply/divide)
- `greet` — a personalized greeting including actor info
- `get_status` — property/trust/subscription counts for the actor
- `echo` — echoes the input back, for testing
- `search` — searches the actor's own properties by keyword (`"*"` lists
  all); sensitive properties (email, tokens) are excluded
- `schedule_task` — schedules a task for a 1X NEO robot integration demo

  ```bash
  curl -X POST https://demo.actingweb.io/{actor_id}/methods/calculate \
       -H "Content-Type: application/json" \
       -d '{"a": 10, "b": 5, "operation": "multiply"}'
  ```

**Actions** — operations with an external effect (`POST
/{actor_id}/actions/{name}`)

- `log_message` — logs a message at a given level
- `send_notification` — simulates sending an email/SMS/push notification

  ```bash
  curl -X POST https://demo.actingweb.io/{actor_id}/actions/log_message \
       -H "Content-Type: application/json" \
       -d '{"message": "Hello from an action", "level": "info"}'
  ```

**Callbacks** — endpoints for external services to notify an actor (`POST
/{actor_id}/callbacks/{name}`), separate from the ActingWeb protocol's own
trust/subscription callbacks

- `email_verify` — validates an emailed verification token
- `sms_webhook` — receives an incoming SMS (Twilio-style payload)
- `payment_webhook` — receives a payment event (Stripe-style payload)
- `bot` (application-level, no actor context: `POST /bot`)

**Property Hooks** — intercept property reads/writes automatically

- `email` — hidden from GET, validated and lowercased on write, protected
  from deletion
- `auth_token` — hidden from GET, blocked from write and delete entirely
- `created_at`, `actor_type` — protected from deletion
- wildcard (`*`) — coerces JSON-looking strings into objects on write for
  every other property

**Lifecycle Hooks** — react to actor events automatically, not directly
callable: `actor_created`, `actor_deleted`, `oauth_success`, plus trust and
subscription lifecycle hooks.

## API Explorer

A web UI for exercising all of the above from a browser is at
`/{actor_id}/www/demo` once you've logged in and an actor exists.

## Running locally

1. Clone with submodules (or run `git submodule update --init` after a plain
   clone):

   ```bash
   git clone --recurse-submodules https://github.com/actingweb/actingwebdemo.git
   ```

   `vendor/actingweb` is a **shallow** submodule pinned to a branch of the
   `actingweb` repo (see `.gitmodules`) — it's a snapshot for running the
   demo locally, not a full history you're expected to work in. If you need
   to change the application code itself, do that in the `actingweb` repo.

2. Copy `.env.example` (in `vendor/actingweb/examples/demo/`) to `.env` at
   this repo's root and fill in an OAuth2 client ID/secret — see
   [OAUTH_SETUP.md](OAUTH_SETUP.md). Never commit `.env`.

3. Bring up DynamoDB Local and the app with Docker Compose:

   ```bash
   docker-compose up -d
   ```

   Or run directly with Poetry:

   ```bash
   poetry install
   poetry run python application.py
   ```

4. Visit `http://localhost:5000`.

**Exposing the app publicly** (to test OAuth2 redirects or webhooks): use
ngrok or similar, and update `APP_HOST_FQDN`/`APP_HOST_PROTOCOL` to match the
public URL — OAuth2 redirect URIs are derived from those two variables.

## Running tests

```bash
poetry install
poetry run pytest tests/ -v
```

CI (`.github/workflows/tests.yml`) runs these against a real DynamoDB Local
instance on every push and pull request.

## OAuth2 configuration

See [OAUTH_SETUP.md](OAUTH_SETUP.md) for setting up Google or GitHub OAuth2
credentials for this app.

## Deployment (AWS Lambda)

Deployment uses the [Serverless Framework](https://serverless.com) v3 and is
handled by `.github/workflows/deploy.yml`, which runs automatically on every
push to `master` and can also be triggered manually
(`workflow_dispatch`).

The workflow **never deploys against an unreleased `actingweb` version**: it
resolves a version (the latest release by default, or an explicit tag via
`workflow_dispatch`), verifies that version is actually published on PyPI
(or TestPyPI, if selected), and only then checks out `actingweb` at that
exact tag into `vendor/actingweb` for the build — independent of whatever
branch the repo's own `.gitmodules` pin tracks day to day. If the requested
version isn't published, the workflow fails before touching AWS.

Required repository secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
`OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `NUKE_SECRET`. Optional repository
variable: `OAUTH_PROVIDER` (defaults to `google`).

To deploy manually from a checkout with the AWS CLI already configured:

```bash
export OAUTH_CLIENT_ID="..."
export OAUTH_CLIENT_SECRET="..."
export OAUTH_PROVIDER="google"  # or "github"
serverless deploy
```

`serverless.yml`'s `package.patterns` includes only
`vendor/actingweb/examples/demo/**` from the submodule — the rest of the
vendored `actingweb` repo (its own `actingweb/` package source, tests, docs)
is excluded, since the actual `actingweb` package is installed separately
via Poetry.

## The `/nuke` endpoint

`GET /nuke?secret=<NUKE_SECRET>` deletes every actor in the deployment's
DynamoDB tables. It exists to reset the public demo between QA passes and is
gated behind the `NUKE_SECRET` environment variable — leave it unset to
disable the endpoint. This is a destructive test-cleanup tool, not something
to expose without that secret.

## Using the library for your own project

This repo is a deployment example, not a starting point for your own
ActingWeb app — for that, see the
[`actingweb` library](https://github.com/actingweb/actingweb) and its
`examples/demo/` (the code this repo vendors and deploys).
