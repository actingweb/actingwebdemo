"""
Shared method hooks for ActingWeb demo applications.

These hooks handle RPC-style method calls.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from actingweb.interface.actor_interface import ActorInterface

logger = logging.getLogger(__name__)


def register_method_hooks(app):
    """Register all method hooks with the ActingWeb application."""

    @app.method_hook("calculate")
    def handle_calculate_method(
        actor: ActorInterface, method_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle calculate method with JSON-RPC support."""
        try:
            a = data.get("a", 0)
            b = data.get("b", 0)
            operation = data.get("operation", "add")

            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return None  # Division by zero
                result = a / b
            else:
                return None  # Unsupported operation

            return {"result": result, "operation": operation}
        except (TypeError, ValueError):
            return None

    @app.method_hook("greet")
    def handle_greet_method(
        actor: ActorInterface, method_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle greet method with personalized greeting."""
        name = data.get("name", "World")
        actor_id = actor.id if actor else "unknown"

        # Determine which framework is being used based on app context
        integration = "unknown"
        if hasattr(app, "_flask_app"):
            integration = "Flask"
        elif hasattr(app, "_fastapi_app"):
            integration = "FastAPI"

        return {
            "greeting": f"Hello, {name}! This is actor {actor_id} via {integration}.",
            "timestamp": datetime.now().isoformat(),
            "integration": integration,
        }

    @app.method_hook("get_status")
    def handle_get_status_method(
        actor: ActorInterface, method_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle get_status method to return actor status."""
        if not actor:
            return None

        return {
            "actor_id": actor.id,
            "creator": actor.creator,
            "status": "active",
            "properties_count": len(actor.properties.to_dict())
            if actor.properties is not None
            else 0,
            "trust_relationships": len(actor.trust.relationships),
            "subscriptions": len(actor.subscriptions.all_subscriptions),
        }
