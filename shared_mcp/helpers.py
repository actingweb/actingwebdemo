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
        description="Search through stored data and return relevant results",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string to match against stored data",
                }
            },
            "required": ["query"],
        },
    )
    def handle_search(actor, action_name: str, data: Dict[str, Any]) -> list:
        """Search through all stored data - follows OpenAI MCP specification for search tool."""
        query = data.get("query", "").strip()
        
        if not query:
            return []
        
        # Use the existing search function with default settings
        result = search_actor_data(actor, query, "all", 20)
        
        if result.get("status") != "success" or not result.get("results"):
            return []
        
        # Convert to OpenAI MCP format
        search_results = []
        for item in result["results"]:
            item_type = item.get("type", "unknown")
            item_id = item.get("id")
            
            # Create fetch ID for this item
            fetch_id = f"{item_type}:{item_id}" if item_id else f"{item_type}:unknown"
            
            # Format according to OpenAI MCP specification
            search_result = {
                "id": fetch_id,
                "title": item.get("title", f"{item_type.capitalize()} {item_id}"),
                "text": _create_search_snippet(item, query),
                "url": f"#{item_type}-{item_id}" if item_id else f"#{item_type}"
            }
            search_results.append(search_result)
        
        return search_results

    @app.action_hook("fetch")
    @mcp_tool(
        description="Retrieve the full contents of a search result document or item by ID",
        input_schema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string", 
                    "description": "A unique identifier for the search document (format: 'type:id' e.g., 'note:1' or 'reminder:2')"
                }
            },
            "required": ["id"],
        },
    )
    def handle_fetch(actor, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch specific data items - follows OpenAI MCP specification for fetch tool."""
        fetch_id = data.get("id", "")
        
        if not fetch_id:
            return {"error": "ID is required"}
        
        # Parse the ID format "type:id" (e.g., "note:1", "reminder:2")
        if ":" not in fetch_id:
            return {"error": "Invalid ID format. Expected format: 'type:id' (e.g., 'note:1' or 'reminder:2')"}
        
        try:
            fetch_type, item_id_str = fetch_id.split(":", 1)
            item_id = int(item_id_str)
        except (ValueError, TypeError):
            return {"error": f"Invalid ID format: {fetch_id}. Expected format: 'type:id' with numeric ID"}
        
        # Fetch the specific item
        result = fetch_actor_data(actor, fetch_type, item_id, 1, {})
        
        if result.get("status") == "success" and "data" in result:
            item = result["data"]
            # Format according to OpenAI MCP specification
            return {
                "id": fetch_id,
                "title": item.get("title", f"{fetch_type.capitalize()} {item_id}"),
                "text": f"{item.get('content', item.get('description', ''))}",
                "url": f"#{fetch_type}-{item_id}",  # Internal reference
                "metadata": {
                    "type": fetch_type,
                    "item_id": item_id,
                    "created_at": item.get("created_at"),
                    "priority": item.get("priority"),
                    "tags": item.get("tags", []) if fetch_type == "note" else None,
                    "due_date": item.get("due_date") if fetch_type == "reminder" else None,
                    "completed": item.get("completed") if fetch_type == "reminder" else None
                }
            }
        else:
            return {"error": result.get("error", f"Item not found: {fetch_id}")}

    @app.action_hook("list")
    @mcp_tool(
        description="List collections of data (notes, reminders, stats, recent items)",
        input_schema={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["notes", "reminders", "stats", "recent"],
                    "description": "Type of data collection to list",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of items to return",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
                "filter": {
                    "type": "object",
                    "description": "Optional filters for the collection",
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
    def handle_list(actor, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """List collections of data - provides browsable lists for MCP clients."""
        list_type = data.get("type")
        limit = min(data.get("limit", 20), 100)
        filters = data.get("filter", {})
        
        # Map list types to fetch types
        fetch_type_map = {
            "notes": "notes_all",
            "reminders": "reminders_all",
            "stats": "stats",
            "recent": "recent"
        }
        
        fetch_type = fetch_type_map.get(list_type)
        if not fetch_type:
            return {"error": f"Unknown list type: {list_type}"}
        
        result = fetch_actor_data(actor, fetch_type, None, limit, filters)
        
        # For list operations, include IDs in a format suitable for fetch tool
        if result.get("status") == "success" and "data" in result:
            if list_type in ["notes", "reminders"]:
                # Add fetch IDs to each item
                items = result["data"]
                if isinstance(items, list):
                    for item in items:
                        item_id = item.get("id")
                        if item_id:
                            item["fetch_id"] = f"{list_type[:-1]}:{item_id}"  # "notes" -> "note:1"
        
        return result

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


def _create_search_snippet(item: Dict[str, Any], query: str) -> str:
    """Create a relevant text snippet for search results."""
    content = item.get("content", item.get("description", ""))
    title = item.get("title", "")
    
    # If content is short, return it as-is
    if len(content) <= 150:
        return content
    
    # Try to find the query in the content for context
    query_lower = query.lower()
    content_lower = content.lower()
    
    # Find query position and extract surrounding context
    query_pos = content_lower.find(query_lower)
    if query_pos != -1:
        # Extract ~75 chars before and after the query
        start = max(0, query_pos - 75)
        end = min(len(content), query_pos + len(query) + 75)
        snippet = content[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
            
        return snippet
    
    # If query not found, return first 150 chars
    return content[:150] + ("..." if len(content) > 150 else "")


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
    Only registers MCP functionality if MCP is enabled in the app configuration.
    
    Args:
        app: ActingWeb application instance to register functionality with
    """
    # Check if MCP is enabled before registering functionality
    if hasattr(app, 'is_mcp_enabled') and not app.is_mcp_enabled():
        print("MCP functionality disabled - skipping MCP registration")
        return
        
    register_common_mcp_tools(app)
    register_common_mcp_prompts(app)