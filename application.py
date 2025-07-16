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
from typing import Any, Dict, Optional, List, Union

# Configure logging
logging.basicConfig(stream=sys.stderr, level=os.getenv("LOG_LEVEL", "INFO"))
LOG = logging.getLogger()
LOG.setLevel(os.getenv("LOG_LEVEL", "INFO"))

# Create Flask app
flask_app = Flask(__name__, static_url_path="/static")

# Create ActingWeb app with fluent configuration
app = (
    ActingWebApp(
        aw_type="urn:actingweb:actingweb.org:actingwebdemo",
        database="dynamodb",
        fqdn=os.getenv("APP_HOST_FQDN", "greger.ngrok.io"),
        proto=os.getenv("APP_HOST_PROTOCOL", "https://"),
    )
    .with_oauth(
        client_id=os.getenv("APP_OAUTH_ID", ""),
        client_secret=os.getenv("APP_OAUTH_KEY", ""),
        scope="",
        auth_uri="https://api.actingweb.net/v1/authorize",
        token_uri="https://api.actingweb.net/v1/access_token",
    )
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


# Actor factory
@app.actor_factory
def create_actor(creator: str, **kwargs) -> ActorInterface:
    """Create a new actor instance with default properties."""
    actor = ActorInterface.create(creator=creator, config=app.get_config())

    # Initialize actor properties
    if actor.properties is not None:
        actor.properties.email = creator
        actor.properties.created_at = str(datetime.now())
        actor.properties.version = "2.3"

    return actor


# Property hooks for access control and validation
@app.property_hook("email")
def handle_email_property(actor: ActorInterface, operation: str, value: Any, path: List[str]) -> Optional[Any]:
    """Handle email property with access control."""
    if operation == "get":
        # Hide email from external access
        return None
    elif operation == "put":
        # Validate email format
        if isinstance(value, str) and "@" in value:
            return value.lower()
        return None
    elif operation == "post":
        # Same validation for POST
        if isinstance(value, str) and "@" in value:
            return value.lower()
        return None
    elif operation == "delete":
        # Protect email from deletion
        return None
    return value


@app.property_hook("*")
def handle_all_properties(actor: ActorInterface, operation: str, value: Any, path: List[str]) -> Optional[Any]:
    """Handle all properties with general validation."""
    if not path:
        return value

    property_name = path[0] if path else ""

    # Apply protection rules
    if property_name in PROP_PROTECT:
        if operation == "delete":
            return None
        elif operation == "put" and property_name in PROP_HIDE:
            return None
        elif operation == "post" and property_name in PROP_HIDE:
            return None

    # Handle JSON string conversion
    import json

    if operation in ["put", "post"]:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        elif not isinstance(value, dict):
            return None

    return value


# Callback hooks
@app.callback_hook("bot")
def handle_bot_callback(actor: ActorInterface, name: str, data: Dict[str, Any]) -> bool:
    """Handle bot callbacks."""
    if data.get("method") == "POST":
        # Safety valve - make sure bot is configured
        config = app.get_config()
        if not config or not config.bot or not config.bot.get("token") or len(config.bot.get("token", "")) == 0:
            return False

        # Process bot request
        LOG.debug("Bot callback received")
        return True
    return False


@app.callback_hook("ping")
def handle_ping_callback(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Union[Dict[str, Any], bool]:
    """Handle ping callback for health checks."""
    if data.get("method") == "GET":
        return {"status": "pong", "actor_id": actor.id, "timestamp": str(datetime.now())}
    return False


@app.callback_hook("status")
def handle_status_callback(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Union[Dict[str, Any], bool]:
    """Handle status callback."""
    if data.get("method") == "GET":
        return {
            "status": "active",
            "actor_id": actor.id,
            "creator": actor.creator,
            "properties": len(actor.properties.to_dict()) if actor.properties is not None else 0,
            "trust_relationships": len(actor.trust.relationships),
            "subscriptions": len(actor.subscriptions.all_subscriptions),
        }
    return False


# Subscription hooks
@app.subscription_hook
def handle_subscription_callback(
    actor: ActorInterface, subscription: Dict[str, Any], peer_id: str, data: Dict[str, Any]
) -> bool:
    """Handle subscription callbacks from other actors."""
    LOG.debug(
        f"Got callback and processed {subscription.get('subscriptionid', 'unknown')} "
        f"subscription from peer {peer_id} with json blob: {data}"
    )

    # Process subscription data
    if subscription.get("target") == "properties":
        # Handle property changes from peer
        if isinstance(data, dict) and actor.properties is not None:
            for key, value in data.items():
                # Store peer property updates
                actor.properties[f"peer_{peer_id}_{key}"] = value

    return True


# Lifecycle hooks
@app.lifecycle_hook("actor_created")
def on_actor_created(actor: ActorInterface, **kwargs: Any) -> None:
    """Handle actor creation."""
    LOG.info(f"New actor created: {actor.id} for {actor.creator}")

    # Set initial properties
    if actor.properties is not None:
        actor.properties.demo_version = "2.3"
        actor.properties.interface_version = "modern"


@app.lifecycle_hook("actor_deleted")
def on_actor_deleted(actor: ActorInterface, **kwargs: Any) -> None:
    """Handle actor deletion."""
    LOG.info(f"Actor {actor.id} is being deleted")

    # Custom cleanup could be performed here
    # The framework handles standard cleanup automatically


@app.lifecycle_hook("oauth_success")
def on_oauth_success(actor: ActorInterface, **kwargs: Any) -> bool:
    """Handle OAuth success."""
    LOG.info(f"OAuth successful for actor {actor.id}")

    # Store OAuth success timestamp
    if actor.properties is not None:
        actor.properties.oauth_success_at = str(datetime.now())

    return True


# Resource hooks (custom endpoints)
@app.callback_hook("resource_demo")
def handle_demo_resource(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Union[Dict[str, Any], bool]:
    """Handle demo resource endpoint."""
    method = data.get("method", "GET")

    if method == "GET":
        return {"message": "This is a demo resource", "actor_id": actor.id, "timestamp": str(datetime.now())}
    elif method == "POST":
        body = data.get("body", {})
        return {"message": "Demo resource updated", "received_data": body, "actor_id": actor.id}

    return {}


# WWW path hooks
@app.callback_hook("www")
def handle_www_paths(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Union[Dict[str, Any], bool]:
    """Handle custom www paths."""
    path = data.get("path", "")

    if path == "demo":
        return {
            "template": "demo.html",
            "data": {
                "actor_id": actor.id, 
                "creator": actor.creator, 
                "properties": actor.properties.to_dict() if actor.properties is not None else {}
            },
        }

    return False


# Integrate with Flask
integration = app.integrate_flask(flask_app)


# Custom error handlers
@flask_app.errorhandler(404)
def not_found(error):
    return {"error": "Not found"}, 404


@flask_app.errorhandler(500)
def internal_error(error):
    return {"error": "Internal server error"}, 500


if __name__ == "__main__":
    LOG.info("Starting ActingWeb Demo with modern interface...")

    # Run in development mode
    flask_app.run(host="0.0.0.0", port=5000, debug=True)
