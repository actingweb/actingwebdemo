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
# MCP-EXPOSED ACTIONS (Tools)
# =============================================================================

@app.action_hook("send_notification")
@mcp_tool(
    description="Send a notification message to the user with priority level",
    input_schema={
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The notification message to send"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Priority level of the notification",
                "default": "medium"
            },
            "category": {
                "type": "string",
                "description": "Category of notification (e.g., 'system', 'user', 'alert')",
                "default": "user"
            }
        },
        "required": ["message"]
    }
)
def handle_notification(actor: ActorInterface, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Send a notification - exposed as MCP tool."""
    message = data.get("message", "")
    priority = data.get("priority", "medium")
    category = data.get("category", "user")
    
    # Validate message
    if not message.strip():
        return {"error": "Message cannot be empty"}
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    # Store notification in actor properties
    notifications = actor.properties.get("notifications", [])
    notification = {
        "id": len(notifications) + 1,
        "message": message,
        "priority": priority,
        "category": category,
        "timestamp": datetime.now().isoformat(),
        "read": False
    }
    notifications.append(notification)
    actor.properties.notifications = notifications
    
    logger.info(f"MCP Tool: Sent {priority} priority notification: {message}")
    
    return {
        "status": "sent",
        "notification_id": notification["id"],
        "message": message,
        "priority": priority,
        "category": category,
        "total_notifications": len(notifications)
    }


@app.action_hook("set_preference")
@mcp_tool(
    description="Set a user preference setting",
    input_schema={
        "type": "object",
        "properties": {
            "key": {
                "type": "string",
                "description": "The preference key"
            },
            "value": {
                "type": "string",
                "description": "The preference value"
            },
            "description": {
                "type": "string",
                "description": "Optional description of what this preference does"
            }
        },
        "required": ["key", "value"]
    }
)
def handle_set_preference(actor: ActorInterface, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Set user preference - exposed as MCP tool."""
    key = data.get("key", "").strip()
    value = data.get("value", "").strip()
    description = data.get("description", "")
    
    if not key:
        return {"error": "Preference key cannot be empty"}
    
    if not value:
        return {"error": "Preference value cannot be empty"}
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    # Store preference in actor properties
    preferences = actor.properties.get("preferences", {})
    preferences[key] = {
        "value": value,
        "description": description,
        "updated_at": datetime.now().isoformat()
    }
    actor.properties.preferences = preferences
    
    logger.info(f"MCP Tool: Set preference {key} = {value}")
    
    return {
        "status": "success",
        "key": key,
        "value": value,
        "description": description,
        "total_preferences": len(preferences)
    }


@app.action_hook("clear_notifications")
@mcp_tool(
    description="Clear all notifications or notifications of a specific priority",
    input_schema={
        "type": "object",
        "properties": {
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "all"],
                "description": "Priority level to clear, or 'all' for all notifications",
                "default": "all"
            }
        }
    }
)
def handle_clear_notifications(actor: ActorInterface, action_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Clear notifications - exposed as MCP tool."""
    priority_filter = data.get("priority", "all")
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    notifications = actor.properties.get("notifications", [])
    original_count = len(notifications)
    
    if priority_filter == "all":
        actor.properties.notifications = []
        cleared_count = original_count
    else:
        filtered_notifications = [n for n in notifications if n.get("priority") != priority_filter]
        actor.properties.notifications = filtered_notifications
        cleared_count = original_count - len(filtered_notifications)
    
    logger.info(f"MCP Tool: Cleared {cleared_count} notifications (filter: {priority_filter})")
    
    return {
        "status": "success",
        "cleared_count": cleared_count,
        "remaining_count": len(actor.properties.get("notifications", [])),
        "priority_filter": priority_filter
    }


# =============================================================================
# MCP-EXPOSED METHODS (Prompts)
# =============================================================================

@app.method_hook("generate_greeting")
@mcp_prompt(
    description="Generate a personalized greeting message",
    arguments=[
        {
            "name": "name",
            "description": "The person's name to greet",
            "required": True
        },
        {
            "name": "style",
            "description": "Style of greeting (formal, casual, friendly, professional)",
            "required": False
        },
        {
            "name": "time_of_day",
            "description": "Time of day for context (morning, afternoon, evening)",
            "required": False
        }
    ]
)
def handle_greeting_prompt(actor: ActorInterface, method_name: str, data: Dict[str, Any]) -> str:
    """Generate greeting prompt - exposed as MCP prompt."""
    name = data.get("name", "there")
    style = data.get("style", "friendly")
    time_of_day = data.get("time_of_day", "")
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    # Generate time-based greeting if time_of_day is provided
    time_greeting = ""
    if time_of_day:
        time_greetings = {
            "morning": "Good morning",
            "afternoon": "Good afternoon", 
            "evening": "Good evening"
        }
        time_greeting = time_greetings.get(time_of_day.lower(), "Hello")
    else:
        time_greeting = "Hello"
    
    # Generate style-based greeting
    if style == "formal":
        greeting = f"{time_greeting}, {name}. I hope you are well today."
    elif style == "casual":
        greeting = f"Hey {name}! What's up?"
    elif style == "professional":
        greeting = f"{time_greeting}, {name}. Thank you for connecting with us."
    else:  # friendly (default)
        greeting = f"{time_greeting} {name}! Nice to meet you!"
    
    logger.info(f"MCP Prompt: Generated {style} greeting for {name}")
    
    return greeting


@app.method_hook("create_task_list")
@mcp_prompt(
    description="Create a task list prompt based on project requirements",
    arguments=[
        {
            "name": "project_name", 
            "description": "Name of the project",
            "required": True
        },
        {
            "name": "task_count",
            "description": "Number of tasks to generate (1-20)",
            "required": False
        },
        {
            "name": "priority_level",
            "description": "Priority level for tasks (low, medium, high)",
            "required": False
        },
        {
            "name": "deadline",
            "description": "Project deadline for context",
            "required": False
        }
    ]
)
def handle_task_list_prompt(actor: ActorInterface, method_name: str, data: Dict[str, Any]) -> str:
    """Generate task list prompt - exposed as MCP prompt."""
    project_name = data.get("project_name", "Unnamed Project")
    task_count = min(max(int(data.get("task_count", 5)), 1), 20)  # Limit 1-20
    priority_level = data.get("priority_level", "medium")
    deadline = data.get("deadline", "")
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    prompt = f"Create a comprehensive task list for the project '{project_name}' with {task_count} tasks. "
    prompt += f"Each task should be {priority_level} priority, specific, actionable, and have a clear outcome. "
    
    if deadline:
        prompt += f"Consider the project deadline of {deadline} when structuring tasks. "
    
    prompt += "Format the tasks as a numbered list with brief descriptions and estimated time requirements. "
    prompt += "Include any dependencies between tasks and suggest a logical order of execution."
    
    logger.info(f"MCP Prompt: Generated task list prompt for {project_name}")
    
    return prompt


@app.method_hook("generate_status_report")
@mcp_prompt(
    description="Generate a status report prompt based on actor state",
    arguments=[
        {
            "name": "report_type",
            "description": "Type of report (daily, weekly, project, system)",
            "required": False
        },
        {
            "name": "include_metrics",
            "description": "Whether to include usage metrics",
            "required": False
        }
    ]
)
def handle_status_report_prompt(actor: ActorInterface, method_name: str, data: Dict[str, Any]) -> str:
    """Generate status report prompt - exposed as MCP prompt."""
    report_type = data.get("report_type", "daily")
    include_metrics = data.get("include_metrics", "true").lower() == "true"
    
    # Increment MCP usage counter
    actor.properties.mcp_usage_count = actor.properties.get("mcp_usage_count", 0) + 1
    
    # Gather actor statistics
    notifications = actor.properties.get("notifications", [])
    preferences = actor.properties.get("preferences", {})
    mcp_usage = actor.properties.get("mcp_usage_count", 0)
    created_at = actor.properties.get("created_at", "unknown")
    
    prompt = f"Generate a {report_type} status report for actor {actor.id}. "
    prompt += f"The actor was created at {created_at} and has {len(notifications)} notifications "
    prompt += f"and {len(preferences)} user preferences configured. "
    
    if include_metrics:
        prompt += f"MCP usage count is {mcp_usage}. "
        
        # Add notification breakdown
        if notifications:
            priority_counts: Dict[str, int] = {}
            for notif in notifications:
                priority = notif.get("priority", "unknown")
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            prompt += f"Notification breakdown: {dict(priority_counts)}. "
    
    prompt += "Format as a professional report with sections for Overview, Current Status, "
    prompt += "Key Metrics (if requested), and Recommendations for improvement."
    
    logger.info(f"MCP Prompt: Generated {report_type} status report prompt")
    
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
        "tools_count": 3,  # send_notification, set_preference, clear_notifications
        "prompts_count": 3,  # generate_greeting, create_task_list, generate_status_report
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