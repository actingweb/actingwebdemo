#!/usr/bin/env python3
"""
WSGI entrypoint for the actingwebdemo deployment.

The actual application code lives in the actingweb library repository at
examples/demo/application.py, pinned via this project's `actingweb`
dependency (see pyproject.toml) so the two cannot drift apart. This file
loads that module by its file path and re-exports `app` (the WSGI
callable), so uwsgi.ini's `mount = /=application:app` and serverless.yml's
`custom.wsgi.app: application.app` keep working unchanged.

This resolves the demo module relative to the installed `actingweb`
package's own file location, which only works for an editable/path/git
install where examples/ is actually present on disk (it is deliberately
excluded from the published wheel). Local development currently pins
`actingweb` to a path dependency on a sibling checkout for exactly this
reason -- see pyproject.toml. Once a released version exists to pin to and
this becomes the real deployment, replace this file with the equivalent
resolved against a vendored git submodule instead (see actingweb's
thoughts/plans/2026-08-22-demo-app-consolidation.md, Phase 4).
"""

import importlib.util
import sys
from pathlib import Path

import actingweb

_repo_root = Path(actingweb.__file__).resolve().parent.parent
_demo_application_path = _repo_root / "examples" / "demo" / "application.py"

if not _demo_application_path.exists():
    raise RuntimeError(
        f"Could not find examples/demo/application.py at {_demo_application_path}. "
        "The actingweb dependency must be installed from a source checkout "
        "(a path or editable git install), not a built wheel -- examples/ is "
        "deliberately excluded from the published package."
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
