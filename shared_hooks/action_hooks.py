"""
Shared action hooks for ActingWeb demo applications.

These hooks handle trigger-based functionality and side effects.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from actingweb.interface.actor_interface import ActorInterface

logger = logging.getLogger(__name__)


def register_action_hooks(app):
    """Register all action hooks with the ActingWeb application."""
    
    @app.action_hook("log_message")
    def handle_log_message_action(
        actor: ActorInterface, action_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle log_message action to log a message."""
        message = data.get("message", "")
        level = data.get("level", "info").upper()

        if level == "ERROR":
            logger.error(f"Actor {actor.id if actor else 'unknown'}: {message}")
        elif level == "WARNING":
            logger.warning(f"Actor {actor.id if actor else 'unknown'}: {message}")
        else:
            logger.info(f"Actor {actor.id if actor else 'unknown'}: {message}")

        return {
            "status": "logged", 
            "message": message, 
            "level": level, 
            "timestamp": datetime.now().isoformat()
        }

    @app.action_hook("update_status")
    def handle_update_status_action(
        actor: ActorInterface, action_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle update_status action to update actor status."""
        if not actor:
            return None

        status = data.get("status", "active")
        timestamp = datetime.now().isoformat()

        # Update actor properties
        if actor.properties is not None:
            actor.properties.status = status
            actor.properties.last_update = timestamp

        return {
            "status": "updated", 
            "new_status": status, 
            "timestamp": timestamp, 
            "actor_id": actor.id
        }

    @app.action_hook("send_notification")
    def handle_send_notification_action(
        actor: ActorInterface, action_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle send_notification action (simulated)."""
        recipient = data.get("recipient", "")
        message = data.get("message", "")
        notification_type = data.get("type", "email")

        # Simulate sending notification
        success = bool(recipient and message)

        # Log the notification
        logger.info(f"Sending {notification_type} notification to {recipient}: {message}")

        return {
            "status": "sent" if success else "failed",
            "recipient": recipient,
            "message": message,
            "type": notification_type,
            "timestamp": datetime.now().isoformat(),
        }

    @app.action_hook("notify")
    def handle_notify_action(actor: ActorInterface, name: str, data: Dict[str, Any]) -> bool:
        """Handle notify action triggers."""
        message = data.get("message", "No message provided")
        logger.info(f"Notify action for actor {actor.id}: {message}")

        # Store notification in properties
        notifications = actor.properties.get("notifications", [])
        notifications.append({
            "message": message, 
            "timestamp": datetime.now().isoformat(), 
            "actor_id": actor.id
        })
        actor.properties.notifications = notifications

        return True