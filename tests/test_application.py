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
