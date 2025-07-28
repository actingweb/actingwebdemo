"""
FastAPI demo application for ActingWeb.

This demonstrates how to use ActingWeb with FastAPI for async/await support,
automatic API documentation, and modern Python type safety.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add the actingweb library to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../actingweb"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from actingweb.interface.app import ActingWebApp
from actingweb.interface.actor_interface import ActorInterface

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Properties that should be hidden from external access
PROP_HIDE = ["email"]
PROP_PROTECT = PROP_HIDE + []

# Create FastAPI app
fastapi_app = FastAPI(
    title="ActingWeb FastAPI Demo",
    description="ActingWeb REST API with FastAPI integration",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc documentation
)

# Create ActingWeb app
app = (
    ActingWebApp(
        aw_type="urn:actingweb:actingweb.org:actingwebdemo",
        database="dynamodb",
        fqdn=os.getenv("APP_HOST_FQDN", "greger.ngrok.io"),
        proto=os.getenv("APP_HOST_PROTOCOL", "https://"),
    )
    .with_web_ui(enable=True)
    .with_devtest(enable=True)
    .with_unique_creator(enable=False)
    .with_email_as_creator(enable=False)
    .add_actor_type(
        name="myself",
        factory=f"{os.getenv('APP_HOST_PROTOCOL', 'https://')}{os.getenv('APP_HOST_FQDN', 'greger.ngrok.io')}/",
        relationship="friend",
    )
)

# Add OAuth configuration if available
oauth_client_id = os.getenv("OAUTH_CLIENT_ID")
oauth_client_secret = os.getenv("OAUTH_CLIENT_SECRET")
if oauth_client_id and oauth_client_secret:
    app.with_oauth(
        client_id=oauth_client_id,
        client_secret=oauth_client_secret,
        scope="profile email",
        auth_uri="https://accounts.google.com/o/oauth2/auth",
        token_uri="https://oauth2.googleapis.com/token",
    )

# Add bot configuration (always configure with defaults)
app.with_bot(
    token=os.getenv("APP_BOT_TOKEN", ""),
    email=os.getenv("APP_BOT_EMAIL", ""),
    secret=os.getenv("APP_BOT_SECRET", ""),
    admin_room=os.getenv("APP_BOT_ADMIN_ROOM", ""),
)


@app.actor_factory
def create_actor(creator: str, **kwargs) -> ActorInterface:
    """Create a new actor instance with default properties."""
    logger.info(f"Creating actor for creator: {creator}")
    actor = ActorInterface.create(creator=creator, config=app.get_config())

    # Initialize actor properties
    if actor.properties is not None:
        actor.properties.email = creator
        actor.properties.created_at = str(datetime.now())
        actor.properties.version = "2.3"
        actor.properties.created_via = "fastapi"

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
            logger.info(f"Actor {actor.id} email changed to {value.lower()}")
            return value.lower()
        return None
    elif operation == "post":
        # Same validation for POST
        if isinstance(value, str) and "@" in value:
            logger.info(f"Actor {actor.id} email set to {value.lower()}")
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


@app.callback_hook("ping")
def handle_ping(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle ping callbacks."""
    logger.info(f"Ping callback for actor {actor.id}: {data}")
    return {"status": "pong", "timestamp": data.get("timestamp"), "actor_id": actor.id}


@app.callback_hook("echo")
def handle_echo(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle echo callbacks."""
    logger.info(f"Echo callback for actor {actor.id}: {data}")
    return {"echo": data}


@app.callback_hook("subscription")
def handle_subscription_callback(actor: ActorInterface, name: str, data: Dict[str, Any]) -> bool:
    """Handle subscription callbacks."""
    logger.info(f"Subscription callback for actor {actor.id}: {data}")
    
    # Extract subscription info from the data
    subscription = data.get("subscription", {})
    peerid = data.get("peerid", "")
    
    # Process the subscription callback directly
    logger.debug(f"Processing subscription callback from peer {peerid}: {data}")
    
    # Here you would implement the actual subscription callback logic
    # For now, just log and return success
    return True


# Application-level callback hooks (no actor context)
@app.app_callback_hook("bot")
def handle_bot_callback(data: Dict[str, Any]) -> bool:
    """Handle bot callbacks (application-level, no actor context)."""
    if data.get("method") == "POST":
        # Safety valve - make sure bot is configured
        config = app.get_config()
        if not config or not config.bot or not config.bot.get("token") or len(config.bot.get("token", "")) == 0:
            return False

        # Process bot request
        logger.debug("Bot callback received")
        return True
    return False


@app.method_hook("greet")
def handle_greet_method(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle greet method calls."""
    greeting_name = data.get("name", "World")
    message = f"Hello, {greeting_name}! From actor {actor.id}"
    logger.info(f"Greet method called for actor {actor.id}: {message}")
    return {"message": message, "actor_id": actor.id}


@app.action_hook("notify")
def handle_notify_action(actor: ActorInterface, name: str, data: Dict[str, Any]) -> bool:
    """Handle notify action triggers."""
    message = data.get("message", "No message provided")
    logger.info(f"Notify action triggered for actor {actor.id}: {message}")

    # Store notification in properties
    notifications = actor.properties.notifications = []
    notifications.append({"message": message, "timestamp": data.get("timestamp"), "actor_id": actor.id})
    actor.properties.notifications = notifications

    return True


@app.subscription_hook
def on_subscription_data(actor: ActorInterface, peerid: str, data: Dict[str, Any]) -> bool:
    """Handle incoming subscription data."""
    logger.info(f"Subscription data for actor {actor.id} from {peerid}: {data}")

    # Store subscription data in properties
    sub_data = actor.properties.subscription_data = []
    sub_data.append({"peerid": peerid, "data": data, "actor_id": actor.id})
    actor.properties.subscription_data = sub_data

    return True


@app.lifecycle_hook("actor_created")
def on_actor_created(actor: ActorInterface, **kwargs: Any) -> None:
    """Handle actor creation."""
    logger.info(f"New actor created: {actor.id} for {actor.creator}")

    # Set initial properties
    if actor.properties is not None:
        actor.properties.demo_version = "2.3"
        actor.properties.interface_version = "modern"


@app.lifecycle_hook("actor_deleted")
def on_actor_deleted(actor: ActorInterface, **kwargs: Any) -> None:
    """Handle actor deletion."""
    logger.info(f"Actor {actor.id} is being deleted")

    # Custom cleanup could be performed here
    # The framework handles standard cleanup automatically


@app.lifecycle_hook("oauth_success")
def on_oauth_success(actor: ActorInterface, **kwargs: Any) -> bool:
    """Handle OAuth success."""
    logger.info(f"OAuth successful for actor {actor.id}")

    # Store OAuth success timestamp
    if actor.properties is not None:
        actor.properties.oauth_success_at = str(datetime.now())

    return True


# Mount static files for web UI
if os.path.exists("static"):
    fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")

# Integrate ActingWeb with FastAPI
templates_dir = "templates" if os.path.exists("templates") else None
integration = app.integrate_fastapi(fastapi_app, templates_dir=templates_dir)


@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "integration": "fastapi", "version": "1.0.0"}


if __name__ == "__main__":
    # Run with uvicorn for development
    uvicorn.run("fastapi_application:fastapi_app", host="0.0.0.0", port=5000, reload=True, log_level="debug")
