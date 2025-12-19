"""
Shared callback hooks for ActingWeb demo applications.

Callback hooks handle external callbacks and webhooks. They provide endpoints
for external systems to communicate with actors.

Callbacks are invoked via: POST /{actor_id}/callbacks/{callback_name}
Application-level callbacks: POST /bot (no actor context)

Available Callbacks:
- ping: Health check endpoint, returns "pong"
- echo: Echo back received data (useful for testing)
- status: Return actor status (GET method)
- subscription: Handle subscription notifications from peers
- resource_demo: Demo resource with GET/POST support
- www: Handle custom web UI paths

Application-Level Callbacks (no actor context):
- bot: Handle bot integration callbacks

Subscription Hooks:
- subscription_hook: Process incoming subscription data from trusted peers

Example usage with curl:
    curl -X POST https://host/{actor_id}/callbacks/ping \\
         -H "Content-Type: application/json" \\
         -d '{"timestamp": "2024-01-01T00:00:00Z"}'
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union
from actingweb.interface.actor_interface import ActorInterface

logger = logging.getLogger(__name__)


def register_callback_hooks(app):
    """Register all callback hooks with the ActingWeb application."""

    @app.callback_hook("ping")
    def handle_ping_callback(
        actor: ActorInterface, name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Handle ping callbacks for health checks.

        Endpoint: POST /{actor_id}/callbacks/ping

        Parameters (optional):
            timestamp: Client timestamp to echo back

        Returns:
            {status: "pong", timestamp, actor_id}

        Use this endpoint to verify actor availability and responsiveness.
        """
        logger.info(f"Ping callback for actor {actor.id}: {data}")
        return {
            "status": "pong",
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "actor_id": actor.id,
            "received_at": datetime.now().isoformat(),
        }

    @app.callback_hook("echo")
    def handle_echo_callback(
        actor: ActorInterface, name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Handle echo callbacks - returns received data.

        Endpoint: POST /{actor_id}/callbacks/echo

        Parameters:
            Any JSON data

        Returns:
            {echo: <received_data>}

        Useful for testing callback connectivity and data serialization.
        """
        logger.info(f"Echo callback for actor {actor.id}: {data}")
        return {
            "echo": data,
            "actor_id": actor.id,
            "timestamp": datetime.now().isoformat(),
        }

    @app.callback_hook("status")
    def handle_status_callback(
        actor: ActorInterface, name: str, data: Dict[str, Any]
    ) -> Union[Dict[str, Any], bool]:
        """
        Handle status callback - returns actor status.

        Endpoint: POST /{actor_id}/callbacks/status

        Parameters:
            method: "GET" to retrieve status

        Returns:
            {status, actor_id, creator, properties, trust_relationships, subscriptions}

        Note: Only responds to GET method requests.
        """
        if data.get("method") == "GET":
            return {
                "status": "active",
                "actor_id": actor.id,
                "creator": actor.creator,
                "properties": len(actor.properties.to_dict())
                if actor.properties is not None
                else 0,
                "trust_relationships": len(actor.trust.relationships),
                "subscriptions": len(actor.subscriptions.all_subscriptions),
                "timestamp": datetime.now().isoformat(),
            }
        return False

    @app.callback_hook("subscription")
    def handle_subscription_callback_hook(
        actor: ActorInterface, name: str, data: Dict[str, Any]
    ) -> bool:
        """
        Handle subscription callback notifications.

        Endpoint: POST /{actor_id}/callbacks/subscription

        This callback is invoked when subscription-related events occur,
        such as when a peer sends subscription data updates.

        Parameters:
            peerid: ID of the peer sending the callback
            Additional data depends on subscription type

        Returns:
            True to acknowledge successful processing
        """
        logger.info(f"Subscription callback for actor {actor.id}: {data}")

        # Extract subscription info from the data
        peerid = data.get("peerid", "")

        # Process the subscription callback directly
        logger.debug(f"Processing subscription callback from peer {peerid}: {data}")

        return True

    @app.callback_hook("resource_demo")
    def handle_demo_resource(
        actor: ActorInterface, name: str, data: Dict[str, Any]
    ) -> Union[Dict[str, Any], bool]:
        """
        Handle demo resource endpoint with GET/POST support.

        Endpoint: POST /{actor_id}/callbacks/resource_demo

        Parameters:
            method: "GET" or "POST"
            body: Request body for POST method

        Returns:
            GET: {message, actor_id, timestamp}
            POST: {message, received_data, actor_id}

        Demonstrates how to implement custom resource endpoints.
        """
        method = data.get("method", "GET")

        if method == "GET":
            return {
                "message": "This is a demo resource",
                "actor_id": actor.id,
                "timestamp": datetime.now().isoformat(),
            }
        elif method == "POST":
            body = data.get("body", {})
            return {
                "message": "Demo resource updated",
                "received_data": body,
                "actor_id": actor.id,
                "timestamp": datetime.now().isoformat(),
            }

        return {}

    @app.callback_hook("www")
    def handle_www_paths(
        actor: ActorInterface, name: str, data: Dict[str, Any]
    ) -> Union[Dict[str, Any], bool]:
        """
        Handle custom www paths for web UI extensions.

        Endpoint: GET /{actor_id}/www/{path}

        Parameters:
            path: The sub-path being requested (e.g., "demo")

        Returns:
            For template rendering: {"template": "template-name.html", "data": {...}}
            Dict with JSON response data
            False to fall through to default handling

        Template Rendering:
            When a hook returns {"template": "...", "data": {...}}, the ActingWeb
            Flask integration will render that template with the provided data
            merged with standard template values (id, url, actor_root, actor_www).

        Available Custom Paths:
            - demo: API Explorer page for testing hooks interactively
        """
        path = data.get("path", "")

        if path == "demo":
            # Render the API Explorer template
            # The integration will add standard template values (id, url, etc.)
            return {
                "template": "aw-actor-www-demo.html",
                "data": {},
            }

        return False

    # Application-level callback hooks (no actor context)
    @app.app_callback_hook("bot")
    def handle_bot_callback(data: Dict[str, Any]) -> bool:
        """
        Handle bot callbacks (application-level, no actor context).

        Endpoint: POST /bot

        This callback handles bot integration webhooks. It's called
        at the application level without an actor context.

        Parameters:
            method: HTTP method (only POST is processed)
            body: Bot webhook payload

        Returns:
            True to acknowledge successful processing
            False if bot is not configured or method is not POST

        Configuration Required:
        - APP_BOT_TOKEN environment variable must be set
        """
        if data.get("method") == "POST":
            # Safety valve - make sure bot is configured
            config = app.get_config()
            if (
                not config
                or not config.bot
                or not config.bot.get("token")
                or len(config.bot.get("token", "")) == 0
            ):
                logger.warning("Bot callback received but bot is not configured")
                return False

            # Process bot request
            logger.debug("Bot callback received")
            return True
        return False

    # Subscription hooks - handle incoming subscription data from peers
    @app.subscription_hook
    def handle_subscription_callback(
        actor: ActorInterface,
        subscription: Dict[str, Any],
        peer_id: str,
        data: Dict[str, Any],
    ) -> bool:
        """
        Handle subscription callbacks from other actors.

        Triggered: When a trusted peer sends subscription data

        This hook processes incoming subscription data from actors that
        have established a trust relationship and subscription.

        Parameters:
            actor: The local ActorInterface receiving the data
            subscription: Subscription metadata (subscriptionid, target, etc.)
            peer_id: ID of the peer sending the data
            data: The subscription payload

        Returns:
            True to acknowledge successful processing

        Side effects:
            - Stores peer property updates as 'peer_{peer_id}_{key}'

        Use this to synchronize data between actors or react to
        changes in subscribed peers.
        """
        logger.debug(
            f"Got callback and processed {subscription.get('subscriptionid', 'unknown')} "
            f"subscription from peer {peer_id} with json blob: {data}"
        )

        # Process subscription data
        if subscription.get("target") == "properties":
            # Handle property changes from peer
            if isinstance(data, dict) and actor.properties is not None:
                for key, value in data.items():
                    # Store peer property updates with prefix
                    actor.properties[f"peer_{peer_id}_{key}"] = value
                logger.info(f"Stored {len(data)} property updates from peer {peer_id}")

        return True
