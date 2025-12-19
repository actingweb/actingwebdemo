"""
Shared method hooks for ActingWeb demo applications.

Method hooks handle RPC-style function calls that are read-only operations.
Unlike actions, methods should NOT modify state - they compute and return results.

Methods are invoked via: POST /{actor_id}/methods/{method_name}
with JSON body containing the method parameters.

Available Methods:
- calculate: Perform arithmetic operations (add/subtract/multiply/divide)
- greet: Return a personalized greeting with actor info
- get_status: Return comprehensive actor status summary

Example usage with curl:
    curl -X POST https://host/{actor_id}/methods/calculate \\
         -H "Content-Type: application/json" \\
         -d '{"a": 10, "b": 5, "operation": "multiply"}'

    curl -X POST https://host/{actor_id}/methods/greet \\
         -H "Content-Type: application/json" \\
         -d '{"name": "Alice"}'
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
        """
        Perform arithmetic operations.

        Endpoint: POST /{actor_id}/methods/calculate

        Parameters:
            a (number): First operand (default: 0)
            b (number): Second operand (default: 0)
            operation (str): Operation - "add", "subtract", "multiply", "divide" (default: "add")

        Returns:
            {result, operation} on success
            None on error (division by zero, unsupported operation)

        Example:
            {"a": 10, "b": 5, "operation": "multiply"} -> {"result": 50, "operation": "multiply"}
        """
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
                    return {"error": "Division by zero", "operation": operation}
                result = a / b
            else:
                return {"error": f"Unsupported operation: {operation}", "operation": operation}

            return {"result": result, "operation": operation, "a": a, "b": b}
        except (TypeError, ValueError) as e:
            return {"error": str(e)}

    @app.method_hook("greet")
    def handle_greet_method(
        actor: ActorInterface, method_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Return a personalized greeting with actor information.

        Endpoint: POST /{actor_id}/methods/greet

        Parameters:
            name (str): Name to greet (default: "World")

        Returns:
            {greeting, timestamp, integration}

        Example:
            {"name": "Alice"} -> {"greeting": "Hello, Alice! This is actor abc123 via Flask.", ...}
        """
        name = data.get("name", "World")
        actor_id = actor.id if actor else "unknown"

        # Determine which framework is being used based on app context
        integration = "Flask"  # Default for this demo

        return {
            "greeting": f"Hello, {name}! This is actor {actor_id} via {integration}.",
            "timestamp": datetime.now().isoformat(),
            "integration": integration,
            "actor_id": actor_id,
        }

    @app.method_hook("get_status")
    def handle_get_status_method(
        actor: ActorInterface, method_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Return comprehensive actor status summary.

        Endpoint: POST /{actor_id}/methods/get_status

        Parameters:
            None required

        Returns:
            {actor_id, creator, status, properties_count, trust_relationships, subscriptions}

        This method provides a quick overview of the actor's current state
        including property counts and relationship statistics.
        """
        if not actor:
            return {"error": "Actor not found"}

        return {
            "actor_id": actor.id,
            "creator": actor.creator,
            "status": "active",
            "properties_count": len(actor.properties.to_dict())
            if actor.properties is not None
            else 0,
            "trust_relationships": len(actor.trust.relationships),
            "subscriptions": len(actor.subscriptions.all_subscriptions),
            "timestamp": datetime.now().isoformat(),
        }

    @app.method_hook("echo")
    def handle_echo_method(
        actor: ActorInterface, method_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Echo back the input data (useful for testing).

        Endpoint: POST /{actor_id}/methods/echo

        Parameters:
            Any JSON data

        Returns:
            {echo: <input_data>, actor_id, timestamp}
        """
        return {
            "echo": data,
            "actor_id": actor.id if actor else "unknown",
            "timestamp": datetime.now().isoformat(),
        }
