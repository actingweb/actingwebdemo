#!/usr/bin/env python3
"""
ActingWeb Demo Application using the modern interface.

This demonstrates the new ActingWeb interface with clean, fluent configuration
and decorator-based hooks instead of the old OnAWBase system.
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask
from actingweb.interface import ActingWebApp, ActorInterface

# Add shared functionality to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "shared_hooks"))

# Shared hooks imports
from shared_hooks import register_all_shared_hooks

# Configure logging
logging.basicConfig(stream=sys.stderr, level=os.getenv("LOG_LEVEL", "INFO"))
LOG = logging.getLogger()
LOG.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# Create ActingWeb app with fluent configuration
aw_app = (
    ActingWebApp(
        aw_type="urn:actingweb:actingweb.org:actingwebdemo",
        database="dynamodb",
        fqdn=os.getenv("APP_HOST_FQDN", "greger.ngrok.io"),
        proto=os.getenv("APP_HOST_PROTOCOL", "https://"),
    )
    # OAuth2 configuration - supports Google and GitHub providers via the new authentication system
    # .with_oauth(
    #     client_id=os.getenv(
    #         "OAUTH_CLIENT_ID",
    #         os.getenv("APP_OAUTH_ID", ""),
    #     ),
    #     client_secret=os.getenv("OAUTH_CLIENT_SECRET", os.getenv("APP_OAUTH_KEY", "")),
    #     scope=os.getenv("OAUTH_SCOPE", "openid email profile"),  # Default to Google scopes
    #     auth_uri=os.getenv("OAUTH_AUTH_URI", "https://accounts.google.com/o/oauth2/v2/auth"),
    #     token_uri=os.getenv("OAUTH_TOKEN_URI", "https://oauth2.googleapis.com/token"),
    #     redirect_uri=f"{os.getenv('APP_HOST_PROTOCOL', 'https://')}{os.getenv('APP_HOST_FQDN', 'greger.ngrok.io')}/oauth/callback",
    # )
    .with_web_ui(enable=True)
    .with_devtest(enable=True)  # Set to False in production
    .with_bot(
        token=os.getenv("APP_BOT_TOKEN", ""),
        email=os.getenv("APP_BOT_EMAIL", ""),
        secret=os.getenv("APP_BOT_SECRET", ""),
        admin_room=os.getenv("APP_BOT_ADMIN_ROOM", ""),
    )
    .with_unique_creator(enable=False)
    .with_email_as_creator(enable=False)
    .add_actor_type(
        name="myself",
        factory=f"{os.getenv('APP_HOST_PROTOCOL', 'https://')}{os.getenv('APP_HOST_FQDN', 'greger.ngrok.io')}/",
        relationship="friend",
    )
)

# Properties that should be hidden from external access
PROP_HIDE = ["email"]
PROP_PROTECT = PROP_HIDE + []

# Register all shared hooks
register_all_shared_hooks(aw_app)

# Create Flask app
app = Flask(__name__, static_url_path="/static")


# Health check endpoint for monitoring
@app.route("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "integration": "flask", "mcp_enabled": False, "version": "1.0.0-mcp"}


# Custom error handlers
@app.errorhandler(404)
def not_found(error):
    return {"error": "Not found"}, 404


@app.errorhandler(500)
def internal_error(error):
    return {"error": "Internal server error"}, 500


# Integrate with Flask
integration = aw_app.integrate_flask(app)

if __name__ == "__main__":
    LOG.info("Starting ActingWeb Demo...")

    # Run in development mode
    app.run(host="0.0.0.0", port=5000, debug=True)
