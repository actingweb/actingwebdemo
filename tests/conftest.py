"""
Root conftest for actingwebdemo's tests.

Sets safe defaults BEFORE any test module imports application.py, which
constructs the ActingWebApp -- including calling integrate_flask(), which
touches DynamoDB -- at import time. Without AWS_DB_HOST pointing somewhere
safe first, importing application.py can silently reach whatever real AWS
account this machine has default credentials for. Mirrors actingweb's own
tests/conftest.py, which exists for the exact same reason.

pytest_configure runs before any test module is collected/imported, and
os.environ.setdefault() doesn't clobber a real .env a developer has
locally -- application.py's own load_dotenv() call doesn't override
already-set variables either, so these defaults win in both CI (no .env
present) and local runs alike.
"""

import os


def pytest_configure(config):
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-west-1")
    os.environ.setdefault("AWS_DB_PREFIX", "test")
    os.environ.setdefault("AWS_DB_HOST", "http://localhost:8000")
    os.environ.setdefault("OAUTH_CLIENT_ID", "test-client-id")
    os.environ.setdefault("OAUTH_CLIENT_SECRET", "test-client-secret")
