"""
Shared lifecycle hooks for ActingWeb demo applications.

These hooks handle actor lifecycle events like creation, deletion, and OAuth success.
"""

import logging
from datetime import datetime
from typing import Any
from actingweb.interface.actor_interface import ActorInterface

logger = logging.getLogger(__name__)


def register_lifecycle_hooks(app):
    """Register all lifecycle hooks with the ActingWeb application."""

    @app.lifecycle_hook("actor_created")
    def on_actor_created(actor: ActorInterface, **kwargs: Any) -> None:
        """Handle actor creation."""
        logger.info(f"New actor created: {actor.id} for {actor.creator}")

        # Set initial properties
        if actor.properties is not None:
            actor.properties.demo_version = "2.3"
            actor.properties.interface_version = "modern"
            actor.properties.created_at = str(datetime.now())

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
