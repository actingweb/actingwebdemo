#!/usr/bin/env python3
"""
WSGI entrypoint for the actingwebdemo deployment.

The actual application code lives in the actingweb library repository at
examples/demo/application.py. This file loads that module by its file
path from the vendor/actingweb git submodule (see .gitmodules) and
re-exports `app` (the WSGI callable), so uwsgi.ini's
`mount = /=application:app` and serverless.yml's
`custom.wsgi.app: application.app` keep working unchanged.

Resolved relative to *this file's own location* (vendor/actingweb/, a
fixed path), not via the installed `actingweb` package's file location.
examples/ is deliberately excluded from the published wheel, so a plain
pip/poetry-installed actingweb -- which is what a packaged Lambda
artifact actually bundles -- never has it; only the submodule checkout
does, and serverless.yml's package.patterns includes
vendor/actingweb/examples/demo/ explicitly for exactly that reason.
"""

import importlib.util
import sys
from pathlib import Path

_demo_application_path = (
    Path(__file__).resolve().parent
    / "vendor"
    / "actingweb"
    / "examples"
    / "demo"
    / "application.py"
)

if not _demo_application_path.exists():
    raise RuntimeError(
        f"Could not find examples/demo/application.py at {_demo_application_path}. "
        "Run `git submodule update --init` to check out vendor/actingweb."
    )

_spec = importlib.util.spec_from_file_location(
    "_actingwebdemo_application", _demo_application_path
)
assert _spec is not None and _spec.loader is not None
_demo = importlib.util.module_from_spec(_spec)
# Flask(__name__, ...) inside the loaded module resolves its root_path (and
# therefore where it looks for templates/ and static/) via
# sys.modules.get(import_name) -- module_from_spec() does NOT register the
# module there on its own. Without this, Flask can't find the module by
# name, falls through to a cwd-based fallback, and silently serves the
# library's default templates instead of this demo's overrides (found by
# comparing this deployment's rendered pages against demo.actingweb.io's).
sys.modules[_spec.name] = _demo
_spec.loader.exec_module(_demo)

app = _demo.app
aw_app = _demo.aw_app

if __name__ == "__main__":
    _demo.LOG.info(
        "Starting actingwebdemo (delegating to examples/demo/application.py "
        f"at {_demo_application_path})..."
    )
    app.run(host="0.0.0.0", port=5000, debug=True)
