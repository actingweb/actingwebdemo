"""
Shared callback hooks for ActingWeb demo applications.

These hooks handle various callback endpoints and bot integration.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Union
from actingweb.interface.actor_interface import ActorInterface

logger = logging.getLogger(__name__)


def register_callback_hooks(app):
    """Register all callback hooks with the ActingWeb application."""
    
    @app.callback_hook("ping")
    def handle_ping_callback(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle ping callbacks for health checks."""
        logger.info(f"Ping callback for actor {actor.id}: {data}")
        return {
            "status": "pong", 
            "timestamp": data.get("timestamp"), 
            "actor_id": actor.id
        }

    @app.callback_hook("echo")
    def handle_echo_callback(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle echo callbacks."""
        logger.info(f"Echo callback for actor {actor.id}: {data}")
        return {"echo": data}

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

    @app.callback_hook("subscription")
    def handle_subscription_callback_hook(actor: ActorInterface, name: str, data: Dict[str, Any]) -> bool:
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

    @app.callback_hook("resource_demo")
    def handle_demo_resource(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Union[Dict[str, Any], bool]:
        """Handle demo resource endpoint."""
        method = data.get("method", "GET")

        if method == "GET":
            return {
                "message": "This is a demo resource", 
                "actor_id": actor.id, 
                "timestamp": str(datetime.now())
            }
        elif method == "POST":
            body = data.get("body", {})
            return {
                "message": "Demo resource updated", 
                "received_data": body, 
                "actor_id": actor.id
            }

        return {}

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
                    "properties": actor.properties.to_dict() if actor.properties is not None else {},
                },
            }

        return False

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

    # Subscription hooks
    @app.subscription_hook
    def handle_subscription_callback(
        actor: ActorInterface, subscription: Dict[str, Any], peer_id: str, data: Dict[str, Any]
    ) -> bool:
        """Handle subscription callbacks from other actors."""
        logger.debug(
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