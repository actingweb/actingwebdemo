# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

This repo is the deployment shell for the live ActingWeb reference demo at
`demo.actingweb.io`. **It does not own the application code.** The actual
Flask app — hooks, templates, OAuth2 wiring — lives in the `actingweb`
library repository at `examples/demo/`, and is vendored here as a shallow
git submodule at `vendor/actingweb` (pinned in `.gitmodules`).

`application.py` at the repo root is a thin WSGI shim: it loads
`vendor/actingweb/examples/demo/application.py` by file path and re-exports
`app` and `aw_app`, so `uwsgi.ini` and `serverless.yml` have a stable
entrypoint. See the comments in `application.py` for why it's loaded this
way (`importlib.util.spec_from_file_location` + explicit `sys.modules`
registration — needed for Flask's `root_path`/template resolution to work
correctly) rather than imported normally.

To change the actual application behavior (hooks, templates, OAuth flow),
edit the `actingweb` repo's `examples/demo/`, not this checkout — changes
there land here the next time `vendor/actingweb`'s pin is updated.

**This demo has no MCP integration.** It's a pure ActingWeb protocol demo —
OAuth2, methods, actions, callbacks, properties, trust, subscriptions. See
`README.md` for the full list of what it implements.

## Working in this repo

```bash
git submodule update --init          # check out vendor/actingweb (do this first)
poetry install                       # install deps, including the path-pinned actingweb
poetry run pytest tests/ -v          # run tests (needs DynamoDB Local, see below)
poetry run ruff check .
poetry run pyright application.py tests/
```

`tests/conftest.py` sets safe DynamoDB/OAuth env defaults so pytest never
touches real AWS by accident. DynamoDB Local for local runs:

```bash
docker-compose up -d
# or, for tests only:
docker compose -f vendor/actingweb/docker-compose.test.yml up dynamodb-test
```

`pyproject.toml` pins `actingweb` as a Poetry **path** dependency onto
`vendor/actingweb` (`develop = false` — Lambda packaging needs a real
installed copy, not an editable `.pth` reference), not a PyPI version,
because `examples/demo/` is deliberately excluded from the published wheel.
Re-run `poetry install` after updating the submodule pin to pick up changes.

## CI and deployment

- `.github/workflows/tests.yml` — lint, type-check, test on every push/PR.
  Explicitly shallow-fetches the submodule (`git submodule update --init
  --depth 1`) rather than relying on `.gitmodules`' `shallow = true` alone,
  which was verified locally to not reliably shallow-fetch on its own.
- `.github/workflows/deploy.yml` — deploys to AWS Lambda via Serverless
  Framework v3 on push to `master`, or on demand. Resolves and verifies a
  specific `actingweb` release is actually published on PyPI/TestPyPI
  *before* checking it out and building, independent of whatever branch
  `vendor/actingweb`'s day-to-day CI pin tracks. Never deploys against an
  unreleased version.

Deployment (Elastic Beanstalk config, `on_aw.py`, Runscope tests) that used
to exist in this repo has been removed — Serverless/Lambda is the only
deployment path in use, and tests run via pytest against DynamoDB Local in
CI. See `README.md` for the full deployment story and required secrets.

## Docs

- `README.md` — architecture, running locally, hook reference, deployment
- `OAUTH_SETUP.md` — Google/GitHub OAuth2 app setup for this deployment
- `CHANGELOG.md` — history, including the move to vendoring `actingweb`

For the ActingWeb protocol itself and the library's fluent API, see the
`actingweb` repo's own docs (`docs/`, `CLAUDE.md`).
