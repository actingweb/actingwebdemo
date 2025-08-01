"""
MCP helper functions for ActingWeb demo applications.

This module provides helper functions to register common MCP tools and prompts
using the shared business logic, making it easy to add MCP functionality to
any ActingWeb demo application.
"""

from typing import Dict, Any
from .tools import search_actor_data, fetch_actor_data, create_note, create_reminder
from .prompts import (
    generate_notes_analysis_prompt, 
    generate_learning_prompt, 
    generate_meeting_prep_prompt
)


def register_common_mcp_tools(app) -> None:
    """
    Register common MCP tools with an ActingWeb application.
    
    Args:
        app: ActingWeb application instance to register tools with
    """
    # Import decorators from the core library
    from actingweb.mcp import mcp_tool
    
    @app.action_hook("search")
    @mcp_tool(
        description="Search through stored data including notes, reminders, and other user information",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to match against titles, content, tags, or other text fields",
                },
                "type": {
                    "type": "string",
                    "enum": ["all", "notes", "reminders", "properties"],
                    "description": "Type of data to search through",
                    "default": "all",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                },
            },
            "required": ["query"],
        },
    )
    def handle_search(actor, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Search through all stored data - primary search functionality for MCP clients."""
        query = data.get("query", "").strip()
        search_type = data.get("type", "all")
        limit = min(data.get("limit", 10), 50)
        
        return search_actor_data(actor, query, search_type, limit)
    
    
    @app.action_hook("fetch")
    @mcp_tool(
        description="Fetch specific items by ID or retrieve collections of data",
        input_schema={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["note", "reminder", "notes_all", "reminders_all", "stats", "recent"],
                    "description": "Type of data to fetch",
                },
                "id": {"type": "integer", "description": "Specific ID to fetch (required for 'note' and 'reminder' types)"},
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of items to return for collection fetches",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
                "filter": {
                    "type": "object",
                    "description": "Optional filters for collection fetches",
                    "properties": {
                        "completed": {"type": "boolean", "description": "Filter reminders by completion status"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                            "description": "Filter by priority",
                        },
                        "tag": {"type": "string", "description": "Filter notes by specific tag"},
                    },
                },
            },
            "required": ["type"],
        },
    )
    def handle_fetch(actor, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch specific data items or collections - primary data retrieval for MCP clients."""
        fetch_type = data.get("type")
        item_id = data.get("id")
        limit = min(data.get("limit", 20), 100)
        filters = data.get("filter", {})
        
        return fetch_actor_data(actor, fetch_type, item_id, limit, filters)
    
    
    @app.action_hook("create_note")
    @mcp_tool(
        description="Create and store a note with optional tags and priority",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The title of the note"},
                "content": {"type": "string", "description": "The content/body of the note"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional tags for categorizing the note",
                    "default": [],
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Priority level of the note",
                    "default": "medium",
                },
            },
            "required": ["title", "content"],
        },
    )
    def handle_create_note(actor, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create and store a note - useful for ChatGPT to help users capture information."""
        title = data.get("title", "")
        content = data.get("content", "")
        tags = data.get("tags", [])
        priority = data.get("priority", "medium")
        
        return create_note(actor, title, content, tags, priority)
    
    
    @app.action_hook("create_reminder")
    @mcp_tool(
        description="Create a time-based reminder or task with due date",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title of the reminder or task"},
                "description": {"type": "string", "description": "Detailed description of what needs to be done"},
                "due_date": {"type": "string", "description": "Due date in ISO format (YYYY-MM-DD) or natural language"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Priority level of the reminder",
                    "default": "medium",
                },
                "category": {
                    "type": "string",
                    "description": "Category for organizing reminders (e.g., 'work', 'personal', 'health')",
                    "default": "general",
                },
            },
            "required": ["title", "due_date"],
        },
    )
    def handle_create_reminder(actor, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a time-based reminder - useful for ChatGPT to help users manage tasks."""
        title = data.get("title", "")
        description = data.get("description", "")
        due_date = data.get("due_date", "")
        priority = data.get("priority", "medium")
        category = data.get("category", "general")
        
        return create_reminder(actor, title, due_date, description, priority, category)


def register_common_mcp_prompts(app) -> None:
    """
    Register common MCP prompts with an ActingWeb application.
    
    Args:
        app: ActingWeb application instance to register prompts with
    """
    # Import decorators from the core library
    from actingweb.mcp import mcp_prompt
    
    @app.method_hook("analyze_notes")
    @mcp_prompt(
        description="Generate an analysis prompt based on stored notes to help find patterns and insights",
        arguments=[
            {
                "name": "analysis_type",
                "description": "Type of analysis (summary, trends, actionable_items, priorities)",
                "required": True,
            },
            {"name": "tag_filter", "description": "Optional tag to filter notes for analysis", "required": False},
            {
                "name": "time_period",
                "description": "Time period to analyze (last_week, last_month, all_time)",
                "required": False,
            },
        ],
    )
    def handle_analyze_notes_prompt(actor, method_name: str, data: Dict[str, Any]) -> str:
        """Generate analysis prompt for stored notes - helps ChatGPT provide insights."""
        analysis_type = data.get("analysis_type", "summary")
        tag_filter = data.get("tag_filter", "")
        time_period = data.get("time_period", "all_time")
        
        return generate_notes_analysis_prompt(actor, analysis_type, tag_filter, time_period)
    
    
    @app.method_hook("create_learning_prompt")
    @mcp_prompt(
        description="Generate a learning-focused prompt to help understand or research a topic",
        arguments=[
            {"name": "topic", "description": "The topic or subject to learn about", "required": True},
            {
                "name": "learning_style",
                "description": "Preferred learning approach (beginner, intermediate, advanced, practical, theoretical)",
                "required": False,
            },
            {
                "name": "focus_area",
                "description": "Specific aspect to focus on (overview, implementation, best_practices, troubleshooting)",
                "required": False,
            },
            {
                "name": "format",
                "description": "Preferred response format (explanation, tutorial, examples, comparison)",
                "required": False,
            },
        ],
    )
    def handle_learning_prompt(actor, method_name: str, data: Dict[str, Any]) -> str:
        """Generate learning-focused prompt - helps ChatGPT provide educational content."""
        topic = data.get("topic", "")
        learning_style = data.get("learning_style", "beginner")
        focus_area = data.get("focus_area", "overview")
        format_type = data.get("format", "explanation")
        
        return generate_learning_prompt(actor, topic, learning_style, focus_area, format_type)
    
    
    @app.method_hook("create_meeting_prep")
    @mcp_prompt(
        description="Generate a meeting preparation prompt based on agenda and participant info",
        arguments=[
            {"name": "meeting_title", "description": "Title or subject of the meeting", "required": True},
            {
                "name": "meeting_type",
                "description": "Type of meeting (standup, review, planning, brainstorm, presentation)",
                "required": False,
            },
            {"name": "participants", "description": "List of participants or roles involved", "required": False},
            {
                "name": "duration",
                "description": "Expected meeting duration (e.g., '30 minutes', '1 hour')",
                "required": False,
            },
            {"name": "key_topics", "description": "Main topics or agenda items to cover", "required": False},
        ],
    )
    def handle_meeting_prep_prompt(actor, method_name: str, data: Dict[str, Any]) -> str:
        """Generate meeting preparation prompt - helps ChatGPT create meeting agendas and prep materials."""
        meeting_title = data.get("meeting_title", "")
        meeting_type = data.get("meeting_type", "general")
        participants = data.get("participants", "")
        duration = data.get("duration", "1 hour")
        key_topics = data.get("key_topics", "")
        
        return generate_meeting_prep_prompt(actor, meeting_title, meeting_type, participants, duration, key_topics)


def register_all_common_mcp_functionality(app) -> None:
    """
    Register all common MCP tools and prompts with an ActingWeb application.
    
    This is a convenience function that registers both tools and prompts.
    
    Args:
        app: ActingWeb application instance to register functionality with
    """
    register_common_mcp_tools(app)
    register_common_mcp_prompts(app)