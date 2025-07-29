"""
ActingWeb MCP Demo Application.

This demonstrates how to use ActingWeb with MCP (Model Context Protocol) integration,
allowing AI language models to interact with ActingWeb actors through standardized
tools, resources, and prompts.

Based on fastapi_application.py with MCP functionality added.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add the actingweb library to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../actingweb"))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from actingweb.interface.app import ActingWebApp
from actingweb.interface.actor_interface import ActorInterface

# MCP integration imports
from actingweb.mcp import mcp_tool, mcp_resource, mcp_prompt

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Properties that should be hidden from external access
PROP_HIDE = ["email", "auth_token"]
PROP_PROTECT = PROP_HIDE + ["created_at", "actor_type"]

# Create FastAPI app
fastapi_app = FastAPI(
    title="ActingWeb MCP Demo",
    description="ActingWeb REST API with MCP (Model Context Protocol) integration",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc documentation
)

# Create ActingWeb app with MCP enabled
app = (
    ActingWebApp(
        aw_type="urn:actingweb:actingweb.org:actingwebdemo-mcp",
        database="dynamodb",
        fqdn=os.getenv("APP_HOST_FQDN", "greger.ngrok.io"),
        proto=os.getenv("APP_HOST_PROTOCOL", "https://"),
    )
    .with_web_ui(enable=True)
    .with_devtest(enable=True)
    # Note: MCP support is enabled by the presence of MCP decorators
    .with_unique_creator(enable=False)
    .with_email_as_creator(enable=False)
    .add_actor_type(
        name="myself",
        factory=f"{os.getenv('APP_HOST_PROTOCOL', 'https://')}{os.getenv('APP_HOST_FQDN', 'greger.ngrok.io')}/",
        relationship="friend",
    )
)

# Add Google OAuth configuration for MCP authentication
# MCP requires OAuth2 with Google to authenticate users and look up actors by email
oauth_client_id = os.getenv("OAUTH_CLIENT_ID")
oauth_client_secret = os.getenv("OAUTH_CLIENT_SECRET")
if oauth_client_id and oauth_client_secret:
    app.with_oauth(
        client_id=oauth_client_id,
        client_secret=oauth_client_secret,
        scope="openid email profile",  # MCP needs email scope to look up actors
        auth_uri="https://accounts.google.com/o/oauth2/v2/auth",
        token_uri="https://oauth2.googleapis.com/token",
    )
    logger.info("Google OAuth configured for MCP authentication")
else:
    logger.warning("Google OAuth not configured - MCP authentication will not work")

# Add bot configuration (always configure with defaults)
app.with_bot(
    token=os.getenv("APP_BOT_TOKEN", ""),
    email=os.getenv("APP_BOT_EMAIL", ""),
    secret=os.getenv("APP_BOT_SECRET", ""),
    admin_room=os.getenv("APP_BOT_ADMIN_ROOM", ""),
)


@app.actor_factory
def create_actor(creator: str, **kwargs) -> ActorInterface:
    """Create a new actor instance with default properties."""
    logger.info(f"Creating MCP-enabled actor for creator: {creator}")
    actor = ActorInterface.create(creator=creator, config=app.get_config())

    # Initialize actor properties
    if actor.properties is not None:
        actor.properties.email = creator
        actor.properties.created_at = str(datetime.now())
        actor.properties.version = "2.3-mcp"
        actor.properties.created_via = "fastapi-mcp"
        actor.properties.mcp_enabled = True
        actor.properties.notifications = []
        actor.properties.preferences = {}
        actor.properties.mcp_usage_count = 0

    return actor


# =============================================================================
# MCP-EXPOSED ACTIONS (Tools) - Simplified to Search and Fetch per OpenAI docs
# =============================================================================

@app.action_hook("search")
@mcp_tool(
    description="Search through stored data including notes, reminders, and other user information",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to match against titles, content, tags, or other text fields"
            },
            "type": {
                "type": "string",
                "enum": ["all", "notes", "reminders", "properties"],
                "description": "Type of data to search through",
                "default": "all"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10,
                "minimum": 1,
                "maximum": 50
            }
        },
        "required": ["query"]
    }
)
def handle_search(actor: ActorInterface, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Search through all stored data - primary search functionality for MCP clients."""
    query = data.get("query", "").strip().lower()
    search_type = data.get("type", "all")
    limit = min(data.get("limit", 10), 50)
    
    if not query:
        return {"error": "Search query cannot be empty"}
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    results = []
    
    # Search notes
    if search_type in ["all", "notes"]:
        notes = actor.properties.get("notes", [])
        for note in notes:
            # Check if query matches title, content, or tags
            title_match = query in note.get("title", "").lower()
            content_match = query in note.get("content", "").lower()
            tag_match = any(query in tag.lower() for tag in note.get("tags", []))
            
            if title_match or content_match or tag_match:
                results.append({
                    "type": "note",
                    "id": note.get("id"),
                    "title": note.get("title"),
                    "content": note.get("content")[:200] + "..." if len(note.get("content", "")) > 200 else note.get("content"),
                    "tags": note.get("tags", []),
                    "priority": note.get("priority"),
                    "created_at": note.get("created_at")
                })
    
    # Search reminders
    if search_type in ["all", "reminders"]:
        reminders = actor.properties.get("reminders", [])
        for reminder in reminders:
            # Check if query matches title or description
            title_match = query in reminder.get("title", "").lower()
            desc_match = query in reminder.get("description", "").lower()
            
            if title_match or desc_match:
                results.append({
                    "type": "reminder",
                    "id": reminder.get("id"),
                    "title": reminder.get("title"),
                    "description": reminder.get("description"),
                    "due_date": reminder.get("due_date"),
                    "priority": reminder.get("priority"),
                    "category": reminder.get("category"),
                    "completed": reminder.get("completed", False),
                    "created_at": reminder.get("created_at")
                })
    
    # Search other properties
    if search_type in ["all", "properties"]:
        # Search through other stored properties for matches
        for key, value in actor.properties.get("custom_data", {}).items():
            if isinstance(value, str) and query in value.lower():
                results.append({
                    "type": "property",
                    "key": key,
                    "value": value[:200] + "..." if len(str(value)) > 200 else str(value)
                })
    
    # Limit results
    results = results[:limit]
    
    logger.info(f"MCP Tool: Found {len(results)} items matching '{query}' in {search_type}")
    
    return {
        "status": "success",
        "query": query,
        "search_type": search_type,
        "results": results,
        "total_found": len(results)
    }


@app.action_hook("fetch")
@mcp_tool(
    description="Fetch specific items by ID or retrieve collections of data",
    input_schema={
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "enum": ["note", "reminder", "notes_all", "reminders_all", "stats", "recent"],
                "description": "Type of data to fetch"
            },
            "id": {
                "type": "integer",
                "description": "Specific ID to fetch (required for 'note' and 'reminder' types)"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of items to return for collection fetches",
                "default": 20,
                "minimum": 1,
                "maximum": 100
            },
            "filter": {
                "type": "object",
                "description": "Optional filters for collection fetches",
                "properties": {
                    "completed": {"type": "boolean", "description": "Filter reminders by completion status"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"], "description": "Filter by priority"},
                    "tag": {"type": "string", "description": "Filter notes by specific tag"}
                }
            }
        },
        "required": ["type"]
    }
)
def handle_fetch(actor: ActorInterface, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch specific data items or collections - primary data retrieval for MCP clients."""
    fetch_type = data.get("type")
    item_id = data.get("id")
    limit = min(data.get("limit", 20), 100)
    filters = data.get("filter", {})
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    # Fetch specific note
    if fetch_type == "note":
        if not item_id:
            return {"error": "ID is required for fetching specific note"}
        
        notes = actor.properties.get("notes", [])
        note = next((n for n in notes if n.get("id") == item_id), None)
        
        if not note:
            return {"error": f"Note with ID {item_id} not found"}
        
        logger.info(f"MCP Tool: Fetched note {item_id}")
        return {
            "status": "success",
            "type": "note",
            "data": note
        }
    
    # Fetch specific reminder
    elif fetch_type == "reminder":
        if not item_id:
            return {"error": "ID is required for fetching specific reminder"}
        
        reminders = actor.properties.get("reminders", [])
        reminder = next((r for r in reminders if r.get("id") == item_id), None)
        
        if not reminder:
            return {"error": f"Reminder with ID {item_id} not found"}
        
        logger.info(f"MCP Tool: Fetched reminder {item_id}")
        return {
            "status": "success",
            "type": "reminder",
            "data": reminder
        }
    
    # Fetch all notes
    elif fetch_type == "notes_all":
        notes = actor.properties.get("notes", [])
        
        # Apply tag filter if specified
        if filters.get("tag"):
            tag_filter = filters["tag"].lower()
            notes = [n for n in notes if tag_filter in [t.lower() for t in n.get("tags", [])]]
        
        # Apply priority filter if specified
        if filters.get("priority"):
            notes = [n for n in notes if n.get("priority") == filters["priority"]]
        
        # Limit results
        notes = notes[:limit]
        
        logger.info(f"MCP Tool: Fetched {len(notes)} notes")
        return {
            "status": "success",
            "type": "notes_collection",
            "data": notes,
            "total_count": len(notes)
        }
    
    # Fetch all reminders
    elif fetch_type == "reminders_all":
        reminders = actor.properties.get("reminders", [])
        
        # Apply completion filter if specified
        if "completed" in filters:
            reminders = [r for r in reminders if r.get("completed", False) == filters["completed"]]
        
        # Apply priority filter if specified
        if filters.get("priority"):
            reminders = [r for r in reminders if r.get("priority") == filters["priority"]]
        
        # Limit results
        reminders = reminders[:limit]
        
        logger.info(f"MCP Tool: Fetched {len(reminders)} reminders")
        return {
            "status": "success",
            "type": "reminders_collection",
            "data": reminders,
            "total_count": len(reminders)
        }
    
    # Fetch usage statistics
    elif fetch_type == "stats":
        notes = actor.properties.get("notes", [])
        reminders = actor.properties.get("reminders", [])
        mcp_usage = actor.properties.get("mcp_usage_count", 0)
        
        # Calculate tag usage
        tag_counts: Dict[str, int] = {}
        for note in notes:
            for tag in note.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        stats = {
            "mcp_usage_count": mcp_usage,
            "total_notes": len(notes),
            "total_reminders": len(reminders),
            "pending_reminders": len([r for r in reminders if not r.get("completed", False)]),
            "completed_reminders": len([r for r in reminders if r.get("completed", False)]),
            "most_used_tags": dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "actor_id": actor.id,
            "created_at": actor.properties.get("created_at", "unknown")
        }
        
        logger.info(f"MCP Tool: Fetched usage statistics")
        return {
            "status": "success",
            "type": "statistics",
            "data": stats
        }
    
    # Fetch recent items
    elif fetch_type == "recent":
        notes = actor.properties.get("notes", [])
        reminders = actor.properties.get("reminders", [])
        
        # Get recent notes (last 5)
        recent_notes = sorted(notes, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
        
        # Get recent reminders (last 5)
        recent_reminders = sorted(reminders, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
        
        logger.info(f"MCP Tool: Fetched recent items")
        return {
            "status": "success",
            "type": "recent_items",
            "data": {
                "recent_notes": recent_notes,
                "recent_reminders": recent_reminders
            }
        }
    
    else:
        return {"error": f"Unknown fetch type: {fetch_type}"}


@app.action_hook("create_note")
@mcp_tool(
    description="Create and store a note with optional tags and priority",
    input_schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the note"
            },
            "content": {
                "type": "string",
                "description": "The content/body of the note"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional tags for categorizing the note",
                "default": []
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Priority level of the note",
                "default": "medium"
            }
        },
        "required": ["title", "content"]
    }
)
def handle_create_note(actor: ActorInterface, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create and store a note - useful for ChatGPT to help users capture information."""
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    tags = data.get("tags", [])
    priority = data.get("priority", "medium")
    
    if not title or not content:
        return {"error": "Both title and content are required"}
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    # Store note in actor properties
    notes = actor.properties.get("notes", [])
    note = {
        "id": len(notes) + 1,
        "title": title,
        "content": content,
        "tags": tags,
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    notes.append(note)
    actor.properties.notes = notes
    
    logger.info(f"MCP Tool: Created note '{title}' with {len(tags)} tags")
    
    return {
        "status": "created",
        "note_id": note["id"],
        "title": title,
        "tags": tags,
        "priority": priority,
        "total_notes": len(notes)
    }


@app.action_hook("create_reminder")
@mcp_tool(
    description="Create a time-based reminder or task with due date",
    input_schema={
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the reminder or task"
            },
            "description": {
                "type": "string",
                "description": "Detailed description of what needs to be done"
            },
            "due_date": {
                "type": "string",
                "description": "Due date in ISO format (YYYY-MM-DD) or natural language"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "urgent"],
                "description": "Priority level of the reminder",
                "default": "medium"
            },
            "category": {
                "type": "string",
                "description": "Category for organizing reminders (e.g., 'work', 'personal', 'health')",
                "default": "general"
            }
        },
        "required": ["title", "due_date"]
    }
)
def handle_create_reminder(actor: ActorInterface, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a time-based reminder - useful for ChatGPT to help users manage tasks."""
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    due_date = data.get("due_date", "").strip()
    priority = data.get("priority", "medium")
    category = data.get("category", "general")
    
    if not title or not due_date:
        return {"error": "Both title and due_date are required"}
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    # Parse due date (simplified - in real app would use dateutil)
    try:
        from datetime import datetime
        # Try to parse ISO format first
        if due_date.count('-') == 2 and len(due_date) >= 10:
            parsed_date = datetime.fromisoformat(due_date[:10])
        else:
            # For natural language, store as-is for now
            parsed_date = None
    except:
        parsed_date = None
    
    # Store reminder in actor properties
    reminders = actor.properties.get("reminders", [])
    reminder = {
        "id": len(reminders) + 1,
        "title": title,
        "description": description,
        "due_date": due_date,
        "parsed_date": parsed_date.isoformat() if parsed_date else None,
        "priority": priority,
        "category": category,
        "completed": False,
        "created_at": datetime.now().isoformat()
    }
    reminders.append(reminder)
    actor.properties.reminders = reminders
    
    logger.info(f"MCP Tool: Created {priority} priority reminder '{title}' due {due_date}")
    
    return {
        "status": "created",
        "reminder_id": reminder["id"],
        "title": title,
        "due_date": due_date,
        "priority": priority,
        "category": category,
        "total_reminders": len(reminders)
    }


# =============================================================================
# MCP-EXPOSED METHODS (Prompts)
# =============================================================================

@app.method_hook("analyze_notes")
@mcp_prompt(
    description="Generate an analysis prompt based on stored notes to help find patterns and insights",
    arguments=[
        {
            "name": "analysis_type",
            "description": "Type of analysis (summary, trends, actionable_items, priorities)",
            "required": True
        },
        {
            "name": "tag_filter",
            "description": "Optional tag to filter notes for analysis",
            "required": False
        },
        {
            "name": "time_period",
            "description": "Time period to analyze (last_week, last_month, all_time)",
            "required": False
        }
    ]
)
def handle_analyze_notes_prompt(actor: ActorInterface, method_name: str, data: Dict[str, Any]) -> str:
    """Generate analysis prompt for stored notes - helps ChatGPT provide insights."""
    analysis_type = data.get("analysis_type", "summary")
    tag_filter = data.get("tag_filter", "")
    time_period = data.get("time_period", "all_time")
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    # Get notes data for context
    notes = actor.properties.get("notes", [])
    note_count = len(notes)
    
    # Filter by tag if specified
    if tag_filter:
        notes = [n for n in notes if tag_filter.lower() in [tag.lower() for tag in n.get("tags", [])]]
    
    # Generate analysis prompt based on type
    if analysis_type == "summary":
        prompt = f"Please analyze and summarize the following {len(notes)} notes"
        if tag_filter:
            prompt += f" tagged with '{tag_filter}'"
        prompt += f" from {time_period.replace('_', ' ')}. Provide key themes, main topics discussed, and overall patterns you observe.\n\n"
    
    elif analysis_type == "trends":
        prompt = f"Analyze the following {len(notes)} notes for trends and patterns"
        if tag_filter:
            prompt += f" in the '{tag_filter}' category"
        prompt += f". Look for recurring themes, evolving ideas, and progression of thoughts over time.\n\n"
    
    elif analysis_type == "actionable_items":
        prompt = f"Review the following {len(notes)} notes and extract actionable items, tasks, and next steps that should be prioritized. Format as a prioritized list with explanations.\n\n"
    
    elif analysis_type == "priorities":
        prompt = f"Analyze the following {len(notes)} notes to identify the most important and urgent items. Help prioritize what should be focused on first.\n\n"
    
    else:
        prompt = f"Please analyze the following {len(notes)} notes and provide insights:\n\n"
    
    # Add note data to prompt
    for i, note in enumerate(notes[:10], 1):  # Limit to 10 notes to avoid too long prompts
        prompt += f"Note {i}:\n"
        prompt += f"Title: {note.get('title', 'Untitled')}\n"
        prompt += f"Content: {note.get('content', '')}\n"
        prompt += f"Tags: {', '.join(note.get('tags', []))}\n"
        prompt += f"Priority: {note.get('priority', 'medium')}\n\n"
    
    if len(notes) > 10:
        prompt += f"... and {len(notes) - 10} more notes with similar content patterns.\n\n"
    
    prompt += f"Based on this data, please provide a {analysis_type} analysis with specific insights and recommendations."
    
    logger.info(f"MCP Prompt: Generated {analysis_type} analysis for {len(notes)} notes")
    
    return prompt


@app.method_hook("create_learning_prompt")
@mcp_prompt(
    description="Generate a learning-focused prompt to help understand or research a topic",
    arguments=[
        {
            "name": "topic", 
            "description": "The topic or subject to learn about",
            "required": True
        },
        {
            "name": "learning_style",
            "description": "Preferred learning approach (beginner, intermediate, advanced, practical, theoretical)",
            "required": False
        },
        {
            "name": "focus_area",
            "description": "Specific aspect to focus on (overview, implementation, best_practices, troubleshooting)",
            "required": False
        },
        {
            "name": "format",
            "description": "Preferred response format (explanation, tutorial, examples, comparison)",
            "required": False
        }
    ]
)
def handle_learning_prompt(actor: ActorInterface, method_name: str, data: Dict[str, Any]) -> str:
    """Generate learning-focused prompt - helps ChatGPT provide educational content."""
    topic = data.get("topic", "").strip()
    learning_style = data.get("learning_style", "beginner")
    focus_area = data.get("focus_area", "overview")
    format_type = data.get("format", "explanation")
    
    if not topic:
        return "Please provide a topic to learn about."
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    # Build learning prompt based on parameters
    prompt = f"I want to learn about {topic} at a {learning_style} level"
    
    if focus_area == "overview":
        prompt += f". Please provide a comprehensive overview covering the key concepts, fundamentals, and why this topic is important."
    elif focus_area == "implementation":
        prompt += f". Focus on practical implementation details, step-by-step processes, and hands-on aspects."
    elif focus_area == "best_practices":
        prompt += f". Emphasize best practices, common patterns, and recommendations from experts in the field."
    elif focus_area == "troubleshooting":
        prompt += f". Focus on common problems, debugging techniques, and solutions to typical challenges."
    else:
        prompt += f" with a focus on {focus_area}."
    
    if format_type == "tutorial":
        prompt += " Present this as a step-by-step tutorial with clear instructions."
    elif format_type == "examples":
        prompt += " Include plenty of concrete examples and code samples where applicable."
    elif format_type == "comparison":
        prompt += " Compare different approaches, tools, or methods related to this topic."
    else:
        prompt += f" Present this as a clear {format_type} with practical insights."
    
    prompt += f" Please structure your response to be educational and actionable for someone at the {learning_style} level."
    
    logger.info(f"MCP Prompt: Generated {learning_style} learning prompt for '{topic}'")
    
    return prompt


@app.method_hook("create_meeting_prep")
@mcp_prompt(
    description="Generate a meeting preparation prompt based on agenda and participant info",
    arguments=[
        {
            "name": "meeting_title",
            "description": "Title or subject of the meeting",
            "required": True
        },
        {
            "name": "meeting_type",
            "description": "Type of meeting (standup, review, planning, brainstorm, presentation)",
            "required": False
        },
        {
            "name": "participants",
            "description": "List of participants or roles involved",
            "required": False
        },
        {
            "name": "duration",
            "description": "Expected meeting duration (e.g., '30 minutes', '1 hour')",
            "required": False
        },
        {
            "name": "key_topics",
            "description": "Main topics or agenda items to cover",
            "required": False
        }
    ]
)
def handle_meeting_prep_prompt(actor: ActorInterface, method_name: str, data: Dict[str, Any]) -> str:
    """Generate meeting preparation prompt - helps ChatGPT create meeting agendas and prep materials."""
    meeting_title = data.get("meeting_title", "").strip()
    meeting_type = data.get("meeting_type", "general")
    participants = data.get("participants", "").strip()
    duration = data.get("duration", "1 hour")
    key_topics = data.get("key_topics", "").strip()
    
    if not meeting_title:
        return "Please provide a meeting title to generate preparation materials."
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    # Get relevant notes and reminders for context
    notes = actor.properties.get("notes", [])
    reminders = actor.properties.get("reminders", [])
    
    # Build meeting prep prompt
    prompt = f"Help me prepare for a {meeting_type} meeting titled '{meeting_title}'"
    
    if duration:
        prompt += f" scheduled for {duration}"
    
    if participants:
        prompt += f" with participants: {participants}"
    
    prompt += ". Please provide:\n\n"
    
    prompt += "1. **Suggested Agenda Structure**: Create a time-based agenda appropriate for a {meeting_type} meeting\n"
    prompt += "2. **Key Discussion Points**: Important topics that should be covered\n"
    prompt += "3. **Preparation Checklist**: What should be prepared beforehand\n"
    prompt += "4. **Success Criteria**: How to measure if the meeting was successful\n"
    
    if key_topics:
        prompt += f"\nSpecific topics to include: {key_topics}\n"
    
    # Add context from stored information
    if notes:
        relevant_notes = [n for n in notes[-5:] if any(word in n.get('content', '').lower() 
                                                     for word in meeting_title.lower().split())]
        if relevant_notes:
            prompt += f"\nRelevant context from recent notes:\n"
            for note in relevant_notes:
                prompt += f"- {note.get('title', 'Untitled')}: {note.get('content', '')[:100]}...\n"
    
    if reminders:
        relevant_reminders = [r for r in reminders if not r.get('completed', False)]
        if relevant_reminders:
            prompt += f"\nOpen reminders that might be relevant:\n"
            for reminder in relevant_reminders[-3:]:
                prompt += f"- {reminder.get('title', '')}: {reminder.get('due_date', '')}\n"
    
    prompt += f"\nPlease tailor the meeting preparation specifically for a {meeting_type} format with {duration} duration."
    
    logger.info(f"MCP Prompt: Generated meeting prep for '{meeting_title}' ({meeting_type})")
    
    return prompt


# =============================================================================
# STANDARD ACTINGWEB HOOKS (Non-MCP)
# =============================================================================

# Property hooks for access control and validation
@app.property_hook("email")
def handle_email_property(actor: ActorInterface, operation: str, value: Any, path: List[str]) -> Optional[Any]:
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
def handle_all_properties(actor: ActorInterface, operation: str, value: Any, path: List[str]) -> Optional[Any]:
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
    import json

    if operation in ["put", "post"]:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        elif not isinstance(value, dict):
            return None

    return value


@app.callback_hook("ping")
def handle_ping(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle ping callbacks."""
    logger.info(f"Ping callback for actor {actor.id}: {data}")
    return {"status": "pong", "timestamp": data.get("timestamp"), "actor_id": actor.id}


@app.callback_hook("echo")
def handle_echo(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle echo callbacks."""
    logger.info(f"Echo callback for actor {actor.id}: {data}")
    return {"echo": data}


# Application-level callback hooks (no actor context)
@app.app_callback_hook("bot")
def handle_bot_callback(data: Dict[str, Any]) -> bool:
    """Handle bot callbacks (application-level, no actor context)."""
    if data.get("method") == "POST":
        # Safety valve - make sure bot is configured
        config = app.get_config()
        if not config or not config.bot or not config.bot.get("token") or len(config.bot.get("token", "")) == 0:
            return False

        # Process bot request
        logger.debug("Bot callback received")
        return True
    return False


# Non-MCP actions and methods for comparison
@app.action_hook("notify")  # Regular action, not exposed to MCP
def handle_notify_action(actor: ActorInterface, name: str, data: Dict[str, Any]) -> bool:
    """Handle notify action triggers (not exposed to MCP)."""
    message = data.get("message", "No message provided")
    logger.info(f"Regular notify action for actor {actor.id}: {message}")

    # Store notification in properties (simpler format than MCP version)
    notifications = actor.properties.get("internal_notifications", [])
    notifications.append({
        "message": message, 
        "timestamp": datetime.now().isoformat(),
        "actor_id": actor.id
    })
    actor.properties.internal_notifications = notifications

    return True


@app.method_hook("greet")  # Regular method, not exposed to MCP
def handle_greet_method(actor: ActorInterface, name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle greet method calls (not exposed to MCP)."""
    greeting_name = data.get("name", "World")
    message = f"Hello, {greeting_name}! From actor {actor.id}"
    logger.info(f"Regular greet method for actor {actor.id}: {message}")
    return {"message": message, "actor_id": actor.id}


# Lifecycle hooks
@app.lifecycle_hook("actor_created")
def on_actor_created(actor: ActorInterface, **kwargs: Any) -> None:
    """Handle actor creation."""
    logger.info(f"New MCP-enabled actor created: {actor.id} for {actor.creator}")

    # Set initial properties
    if actor.properties is not None:
        actor.properties.demo_version = "2.3-mcp"
        actor.properties.interface_version = "modern-mcp"
        actor.properties.mcp_capabilities = ["tools", "prompts"]


@app.lifecycle_hook("actor_deleted")
def on_actor_deleted(actor: ActorInterface, **kwargs: Any) -> None:
    """Handle actor deletion."""
    logger.info(f"MCP-enabled actor {actor.id} is being deleted")


# Mount static files for web UI
if os.path.exists("static"):
    fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")

# Integrate ActingWeb with FastAPI
templates_dir = "templates" if os.path.exists("templates") else None
integration = app.integrate_fastapi(fastapi_app, templates_dir=templates_dir)


@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy", 
        "integration": "fastapi",
        "mcp_enabled": True,
        "version": "1.0.0-mcp"
    }


@fastapi_app.get("/mcp/info")
async def mcp_info():
    """MCP information endpoint."""
    return {
        "mcp_enabled": True,
        "mcp_endpoint": "/mcp",
        "authentication": {
            "type": "oauth2",
            "provider": "google",
            "required_scopes": ["openid", "email", "profile"],
            "flow": "authorization_code",
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token"
        },
        "supported_features": ["tools", "prompts"],
        "tools_count": 4,  # search, fetch, create_note, create_reminder
        "prompts_count": 3,  # analyze_notes, create_learning_prompt, create_meeting_prep
        "actor_lookup": "email_based",
        "description": "ActingWeb MCP Demo - AI can interact with actors through MCP protocol using Google OAuth2"
    }


if __name__ == "__main__":
    logger.info("Starting ActingWeb MCP Demo Application")
    logger.info("MCP endpoint available at: /mcp (requires Google OAuth2)")
    logger.info("MCP authentication flow:")
    logger.info("  1. Client accesses /mcp without Bearer token")
    logger.info("  2. Server returns OAuth2 redirect URL to Google")
    logger.info("  3. User authenticates with Google and grants consent")
    logger.info("  4. Google redirects back with authorization code")
    logger.info("  5. Client exchanges code for Bearer token")
    logger.info("  6. Client uses Bearer token to access /mcp")
    logger.info("  7. Server validates token with Google and looks up actor by email")
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  /mcp/info - MCP configuration information")
    logger.info("  /health - Health check")
    logger.info("  /docs - API documentation")
    
    # Run with uvicorn for development
    uvicorn.run(
        "mcp_application:fastapi_app", 
        host="0.0.0.0", 
        port=5000, 
        reload=True, 
        log_level="debug"
    )