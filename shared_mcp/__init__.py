"""
Shared MCP functionality for ActingWeb demo applications.

This module provides reusable MCP business logic that can be shared
across different ActingWeb demo applications and frameworks.
"""

from .helpers import (
    register_common_mcp_tools,
    register_common_mcp_prompts,
    register_all_common_mcp_functionality
)

__all__ = [
    "register_common_mcp_tools",
    "register_common_mcp_prompts", 
    "register_all_common_mcp_functionality"
]