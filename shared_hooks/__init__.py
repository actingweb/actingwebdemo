"""
Shared hooks for ActingWeb demo applications.

This module provides common hook implementations that are used by both
the Flask and FastAPI demo applications to avoid code duplication.
"""

from .property_hooks import register_property_hooks
from .callback_hooks import register_callback_hooks
from .lifecycle_hooks import register_lifecycle_hooks
from .method_hooks import register_method_hooks
from .action_hooks import register_action_hooks

__all__ = [
    "register_property_hooks",
    "register_callback_hooks",
    "register_lifecycle_hooks",
    "register_method_hooks",
    "register_action_hooks",
    "register_all_shared_hooks",
]


def register_all_shared_hooks(app):
    """
    Register all shared hooks with an ActingWeb application.

    Args:
        app: ActingWebApp instance to register hooks with
    """
    register_property_hooks(app)
    register_callback_hooks(app)
    register_lifecycle_hooks(app)
    register_method_hooks(app)
    register_action_hooks(app)
