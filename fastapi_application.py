"""
ActingWeb FastAPI Demo Application with MCP support.

This demonstrates the ActingWeb framework using FastAPI instead of Flask,
with optional MCP (Model Context Protocol) integration for AI language models.
Similar to application.py but using FastAPI for modern async/await support
and automatic OpenAPI documentation generation.

Features:
- FastAPI integration with automatic OpenAPI docs
- MCP server functionality for AI tool integration
- OAuth2 authentication (Google/GitHub)
- Async request handling
- Built-in Swagger UI at /docs
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add the actingweb library to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../actingweb"))

# Add shared MCP functionality to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "shared_mcp"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "shared_hooks"))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import uvicorn

from actingweb.interface.app import ActingWebApp
from actingweb.interface.actor_interface import ActorInterface

# MCP integration imports
from shared_mcp import register_all_common_mcp_functionality

# Shared hooks imports
from shared_hooks import register_all_shared_hooks

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Properties that should be hidden from external access
PROP_HIDE = ["email", "auth_token"]
PROP_PROTECT = PROP_HIDE + ["created_at", "actor_type"]

# Create FastAPI app with comprehensive documentation
fastapi_app = FastAPI(
    title="ActingWeb FastAPI Demo",
    description="ActingWeb REST API using FastAPI with optional MCP integration",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc documentation
    openapi_tags=[
        {"name": "health", "description": "Health check endpoints"},
        {"name": "actors", "description": "ActingWeb actor operations"},
        {"name": "mcp", "description": "Model Context Protocol integration"},
    ],
)

# Create ActingWeb app with FastAPI integration
app = (
    ActingWebApp(
        aw_type="urn:actingweb:actingweb.org:actingwebdemo-fastapi",
        database="dynamodb",
        fqdn=os.getenv("APP_HOST_FQDN", "greger.ngrok.io"),
        proto=os.getenv("APP_HOST_PROTOCOL", "https://"),
    )
    .with_web_ui(enable=True)
    .with_devtest(enable=True)  # Set to False in production
    .with_mcp(enable=True)  # Enable MCP OAuth2 server functionality
    .with_unique_creator(enable=True)
    .with_email_as_creator(enable=True)
    .add_actor_type(
        name="myself",
        factory=f"{os.getenv('APP_HOST_PROTOCOL', 'https://')}{os.getenv('APP_HOST_FQDN', 'greger.ngrok.io')}/",
        relationship="friend",
    )
)

# Configure OAuth2 authentication (supports Google and GitHub)
oauth_client_id = os.getenv("OAUTH_CLIENT_ID") or os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
oauth_client_secret = os.getenv("OAUTH_CLIENT_SECRET") or os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
oauth_provider = os.getenv("OAUTH_PROVIDER", "google")  # "google" or "github"

if oauth_client_id and oauth_client_secret:
    app.with_oauth(
        client_id=oauth_client_id,
        client_secret=oauth_client_secret,
        scope="openid email profile" if oauth_provider == "google" else "user:email",
        auth_uri="https://accounts.google.com/o/oauth2/v2/auth"
        if oauth_provider == "google"
        else "https://github.com/login/oauth/authorize",
        token_uri="https://oauth2.googleapis.com/token"
        if oauth_provider == "google"
        else "https://github.com/login/oauth/access_token",
        redirect_uri=f"{os.getenv('APP_HOST_PROTOCOL', 'https://')}{os.getenv('APP_HOST_FQDN', 'greger.ngrok.io')}/oauth/callback",
    )

    # Configure OAuth2 provider for the unified authentication system
    try:
        config_obj = app.get_config()
        config_obj.oauth2_provider = oauth_provider
        logger.info(f"OAuth2 provider configured: {oauth_provider}")
    except Exception as e:
        logger.error(f"Failed to configure OAuth2 provider: {e}")

    logger.info(f"{oauth_provider.title()} OAuth2 authentication enabled")
else:
    logger.warning("OAuth2 not configured - set OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET")
    logger.warning("Authentication will fall back to basic auth only")

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
    logger.info(f"Creating actor for creator: {creator}")
    actor = ActorInterface.create(creator=creator, config=app.get_config())

    # Initialize actor properties
    if actor.properties is not None:
        actor.properties.email = creator
        actor.properties.created_at = str(datetime.now())
        actor.properties.version = "2.3-fastapi"
        actor.properties.created_via = "fastapi"
        actor.properties.mcp_enabled = True  # MCP functionality available
        actor.properties.notifications = []
        actor.properties.preferences = {}
        actor.properties.usage_count = 0

    return actor


# Register MCP functionality using shared business logic
register_all_common_mcp_functionality(app)

# Register all shared hooks
register_all_shared_hooks(app)


# Mount static files for web UI
if os.path.exists("static"):
    fastapi_app.mount("/static", StaticFiles(directory="static"), name="static")

# Handle favicon requests to avoid 302 redirects
@fastapi_app.get("/favicon.ico")
@fastapi_app.get("/favicon.png") 
@fastapi_app.get("/favicon.svg")
async def favicon(request: Request):
    """Return favicon or 404 if not found."""
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    import os
    
    # Get the requested favicon type from the path
    requested_path = request.url.path
    favicon_name = requested_path.lstrip('/')
    
    # Try to find the specific favicon first, then fallback to others
    search_order = [favicon_name]
    if favicon_name not in ["favicon.ico", "favicon.png", "favicon.svg"]:
        search_order.extend(["favicon.png", "favicon.ico", "favicon.svg"])
    else:
        # Add other formats as fallbacks
        other_formats = ["favicon.png", "favicon.ico", "favicon.svg"]
        for fmt in other_formats:
            if fmt != favicon_name:
                search_order.append(fmt)
    
    # Search in static directory first, then others
    for directory in ["static", "templates", "."]:
        for fname in search_order:
            favicon_path = os.path.join(directory, fname)
            if os.path.exists(favicon_path):
                return FileResponse(favicon_path, media_type="image/x-icon" if fname.endswith('.ico') else None)
    
    # If no favicon found, return 404 instead of redirect
    raise HTTPException(status_code=404, detail="Favicon not found")

# Handle robots.txt to avoid 302 redirects
@fastapi_app.get("/robots.txt")
async def robots_txt():
    """Return robots.txt or default robots.txt."""
    from fastapi.responses import PlainTextResponse
    import os
    
    # Try to find robots.txt in static directory or root
    for directory in ["static", "."]:
        robots_path = os.path.join(directory, "robots.txt")
        if os.path.exists(robots_path):
            with open(robots_path, 'r') as f:
                return PlainTextResponse(f.read())
    
    # Return default robots.txt
    return PlainTextResponse("""User-agent: *
Disallow: /oauth/
Disallow: /_
Allow: /docs
Allow: /health
Allow: /static/
""", media_type="text/plain")

# Integrate ActingWeb with FastAPI
templates_dir = "templates" if os.path.exists("templates") else None
integration = app.integrate_fastapi(fastapi_app, templates_dir=templates_dir)


@fastapi_app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "integration": "fastapi",
        "mcp_enabled": True,
        "version": "1.0.0",
        "framework": "ActingWeb + FastAPI",
    }


if __name__ == "__main__":
    logger.info("Starting ActingWeb FastAPI Demo Application")
    logger.info("Features: FastAPI integration, MCP support, OAuth2 authentication")
    logger.info("Access Swagger UI at http://localhost:5000/docs")
    logger.info("Access ReDoc at http://localhost:5000/redoc")

    # Run with uvicorn for development
    uvicorn.run("fastapi_application:fastapi_app", host="0.0.0.0", port=5000, reload=True, log_level="debug")
