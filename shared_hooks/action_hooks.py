"""
Shared action hooks for ActingWeb demo applications.

Action hooks handle trigger-based functionality and side effects. Unlike methods
(which are read-only), actions can modify state and trigger external operations.

Actions are invoked via: POST /{actor_id}/actions/{action_name}
with JSON body containing the action parameters.

Available Actions:
- log_message: Log a message at specified level (info/warning/error)
- update_status: Update the actor's status property
- send_notification: Simulate sending a notification (email/sms/push)
- notify: Store a notification message in actor properties
- search: (MCP Tool) Search actor properties by keyword

Example usage with curl:
    curl -X POST https://host/{actor_id}/actions/log_message \\
         -H "Content-Type: application/json" \\
         -d '{"message": "Hello from action", "level": "info"}'
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from actingweb.interface.actor_interface import ActorInterface
from actingweb.mcp import mcp_tool

logger = logging.getLogger(__name__)

# Properties to exclude from MCP search results (sensitive data)
MCP_EXCLUDED_PROPERTIES = ["email", "auth_token", "oauth_token", "access_token", "refresh_token"]


def register_action_hooks(app):
    """Register all action hooks with the ActingWeb application."""

    @app.action_hook("log_message")
    def handle_log_message_action(
        actor: ActorInterface, action_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Log a message at the specified level.

        Endpoint: POST /{actor_id}/actions/log_message

        Parameters:
            message (str): The message to log
            level (str): Log level - "info", "warning", or "error" (default: "info")

        Returns:
            {status, message, level, timestamp}
        """
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
            "timestamp": datetime.now().isoformat(),
        }

    @app.action_hook("update_status")
    def handle_update_status_action(
        actor: ActorInterface, action_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update the actor's status property.

        Endpoint: POST /{actor_id}/actions/update_status

        Parameters:
            status (str): New status value (default: "active")

        Returns:
            {status, new_status, timestamp, actor_id}

        Side effects:
            - Sets actor.properties.status
            - Sets actor.properties.last_update
        """
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
            "actor_id": actor.id,
        }

    @app.action_hook("send_notification")
    def handle_send_notification_action(
        actor: ActorInterface, action_name: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Simulate sending a notification (email, SMS, or push).

        Endpoint: POST /{actor_id}/actions/send_notification

        Parameters:
            recipient (str): Notification recipient (required for success)
            message (str): Notification message (required for success)
            type (str): Notification type - "email", "sms", or "push" (default: "email")

        Returns:
            {status, recipient, message, type, timestamp}

        Note: This is a simulation - no actual notification is sent.
        """
        recipient = data.get("recipient", "")
        message = data.get("message", "")
        notification_type = data.get("type", "email")

        # Simulate sending notification
        success = bool(recipient and message)

        # Log the notification
        logger.info(
            f"Sending {notification_type} notification to {recipient}: {message}"
        )

        return {
            "status": "sent" if success else "failed",
            "recipient": recipient,
            "message": message,
            "type": notification_type,
            "timestamp": datetime.now().isoformat(),
        }

    @app.action_hook("notify")
    def handle_notify_action(
        actor: ActorInterface, name: str, data: Dict[str, Any]
    ) -> bool:
        """
        Store a notification message in the actor's properties.

        Endpoint: POST /{actor_id}/actions/notify

        Parameters:
            message (str): Notification message to store

        Returns:
            True on success

        Side effects:
            - Appends to actor.properties.notifications list
        """
        message = data.get("message", "No message provided")
        logger.info(f"Notify action for actor {actor.id}: {message}")

        # Store notification in properties
        notifications = actor.properties.get("notifications", [])
        if not isinstance(notifications, list):
            notifications = []
        notifications.append(
            {
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "actor_id": actor.id,
            }
        )
        actor.properties.notifications = notifications

        return True

    # MCP Tools - exposed to AI language models via Model Context Protocol

    @app.action_hook("search")
    @mcp_tool(
        description=(
            "Search across this actor's properties by keyword. "
            "Returns matching property names and values. "
            "Use '*' to list all properties. "
            "Sensitive properties like tokens and email are excluded from results."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query - matches against property names and values. Use '*' to list all.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 20)",
                    "default": 20,
                },
            },
            "required": ["query"],
        },
        annotations={
            "readOnlyHint": True,  # Only reads, never modifies
            "destructiveHint": False,  # Doesn't delete data
            "idempotentHint": True,  # Same query = same results
            "openWorldHint": False,  # Doesn't access external services
        },
    )
    def handle_search(
        actor: ActorInterface, action_name: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Search across actor properties by keyword.

        Endpoint: POST /{actor_id}/actions/search
        MCP Tool: search

        Parameters:
            query (str): Search query - use '*' to list all properties
            limit (int): Maximum results to return (default: 20)

        Returns:
            {query, results: [{property, value, match_type}], count, truncated}

        Note: Sensitive properties (email, tokens) are automatically excluded.
        This action is also exposed as an MCP tool for AI assistants.
        """
        query = data.get("query", "").strip().lower()
        limit = data.get("limit", 20)

        if not query:
            return {"error": "Query parameter is required", "results": []}

        # Treat '*' as "list all"
        list_all = query == "*"

        logger.info(f"MCP search for actor {actor.id}: query='{query}', limit={limit}, list_all={list_all}")

        results: List[Dict[str, Any]] = []

        try:
            # Get all properties using to_dict()
            all_props = actor.properties.to_dict() if actor.properties is not None else {}

            if all_props is None:
                all_props = {}

            for prop_name, prop_value in all_props.items():
                # Skip excluded/sensitive properties
                if prop_name in MCP_EXCLUDED_PROPERTIES:
                    continue
                if prop_name.startswith("_"):  # Skip internal properties
                    continue

                # Convert value to string for searching
                value_str = str(prop_value) if prop_value is not None else ""

                # Match all if '*', otherwise check if query matches property name or value
                if list_all or query in prop_name.lower() or query in value_str.lower():
                    results.append({
                        "property": prop_name,
                        "value": prop_value,
                        "match_type": "all" if list_all else ("name" if query in prop_name.lower() else "value"),
                    })

                    if len(results) >= limit:
                        break

            logger.info(f"MCP search found {len(results)} results for '{query}'")

            return {
                "query": query,
                "results": results,
                "count": len(results),
                "truncated": len(results) >= limit,
            }

        except Exception as e:
            logger.error(f"MCP search failed: {e}")
            return {"error": f"Search failed: {str(e)}", "results": []}
