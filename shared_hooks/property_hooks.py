"""
Shared property hooks for ActingWeb demo applications.

These hooks handle property access control, validation, and transformation.
"""

import json
import logging
from typing import Any, List, Optional
from actingweb.interface.actor_interface import ActorInterface

logger = logging.getLogger(__name__)

# Properties that should be hidden from external access
PROP_HIDE = ["email", "auth_token"]
PROP_PROTECT = PROP_HIDE + ["created_at", "actor_type"]


def register_property_hooks(app):
    """Register all property hooks with the ActingWeb application."""

    @app.property_hook("email")
    def handle_email_property(
        actor: ActorInterface, operation: str, value: Any, path: List[str]
    ) -> Optional[Any]:
        """Handle email property with access control."""
        if operation == "get":
            # Hide email from external access
            return None
        elif operation in ["put", "post"]:
            # Validate email format
            if isinstance(value, str) and "@" in value:
                logger.info(f"Actor {actor.id} email changed to {value.lower()}")
                return value.lower()
            return None
        elif operation == "delete":
            # Protect email from deletion
            return None
        return value

    @app.property_hook("*")
    def handle_all_properties(
        actor: ActorInterface, operation: str, value: Any, path: List[str]
    ) -> Optional[Any]:
        """Handle all properties with general validation."""
        if not path:
            return value

        property_name = path[0] if path else ""

        # Apply protection rules
        if property_name in PROP_PROTECT:
            if operation == "delete":
                return None
            elif operation in ["put", "post"] and property_name in PROP_HIDE:
                return None

        # Handle JSON string conversion
        if operation in ["put", "post"]:
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            elif not isinstance(value, dict):
                return None

        return value
