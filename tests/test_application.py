"""
Smoke test for the actingwebdemo WSGI shim (application.py).

Confirms the pin on the actingweb source checkout resolves correctly:
application.py loads examples/demo/application.py from the actingweb
dependency's own file location, and the resulting Flask app is wired up
the way this deployment expects.
"""

import application


def test_application_builds():
    assert application.app is not None
    assert application.aw_app is not None


def test_health_endpoint():
    client = application.app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "healthy"


def test_mcp_is_disabled():
    """This demo is a pure ActingWeb protocol example, not an MCP one."""
    client = application.app.test_client()
    resp = client.get("/mcp")
    assert resp.status_code == 404


def test_search_is_a_method_not_an_action():
    hooks = application.aw_app.hooks
    assert "search" in hooks._method_hooks
    assert "search" not in hooks._action_hooks


def test_templates_resolve_to_the_demo_app_not_the_cwd_or_library_defaults():
    """
    Regression test: Flask(__name__, ...) inside the loaded
    examples/demo/application.py resolves its root_path (and therefore
    where it looks for templates/ and static/) via
    sys.modules.get(import_name). module_from_spec() alone doesn't
    register the module there, so without application.py's explicit
    sys.modules[_spec.name] = _demo line, Flask silently falls back to a
    cwd-based root_path and serves the library's generic default
    templates instead of this demo's branded ones -- found by comparing
    this deployment's rendered pages against demo.actingweb.io's.
    """
    assert application.app.root_path.endswith("examples/demo")

    client = application.app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"ActingWeb Demo" in resp.data
