# ActingWeb Demo Applications

This repository contains two demo applications showcasing the ActingWeb framework with different web frameworks and optional MCP (Model Context Protocol) integration.

## Applications

### 1. Flask Demo (`application.py`)
- **Framework**: Flask
- **Features**: Traditional web application with MCP support
- **URL**: http://localhost:5000
- **Web UI**: Available at `/<actor_id>/www`

### 2. FastAPI Demo (`fastapi_application.py`)
- **Framework**: FastAPI  
- **Features**: Modern async API with automatic OpenAPI docs and MCP support
- **URL**: http://localhost:5000
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

Both applications demonstrate the same ActingWeb functionality but with different web frameworks, allowing you to compare implementations and choose the best fit for your use case.

## Key Features

- **ActingWeb Protocol**: Full implementation of the ActingWeb REST protocol
- **OAuth2 Authentication**: Support for Google and GitHub OAuth2 providers
- **MCP Integration**: Model Context Protocol support for AI language models
- **Actor Management**: Create and manage distributed actor instances
- **Property Storage**: Key-value storage for each actor
- **Trust Relationships**: Manage relationships between actors
- **Subscriptions**: Event subscription system between actors
- **Web UI**: Built-in web interface for actor management

## Quick Start

### Prerequisites
- Python 3.11+
- Poetry (recommended) or pip
- AWS credentials for DynamoDB (or use local DynamoDB)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd actingwebdemo

# Install dependencies with Poetry
poetry install
poetry shell

# Or install with pip
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required
APP_HOST_FQDN=localhost:5000
APP_HOST_PROTOCOL=http://

# OAuth2 (optional but recommended)
OAUTH_PROVIDER=google          # or "github"
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret

# Bot integration (optional)
APP_BOT_TOKEN=your-bot-token
APP_BOT_EMAIL=bot@example.com
APP_BOT_SECRET=bot-secret

# Logging
LOG_LEVEL=INFO
```

### Running the Applications

#### Flask Demo
```bash
python application.py
```

#### FastAPI Demo
```bash
python fastapi_application.py
```

## OAuth2 Setup

### Google OAuth2
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth2 credentials
5. Add redirect URI: `http://localhost:5000/oauth/callback`

### GitHub OAuth2
1. Go to [GitHub Settings > Developer settings](https://github.com/settings/applications/new)
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:5000/oauth/callback`

## API Usage

### Creating an Actor
```bash
# Create a new actor
curl -X POST http://localhost:5000/ \
  -H "Content-Type: application/json" \
  -d '{"creator": "user@example.com"}'
```

### Actor Properties
```bash
# Get actor properties
curl http://localhost:5000/{actor_id}/properties

# Set a property
curl -X PUT http://localhost:5000/{actor_id}/properties/status \
  -H "Content-Type: application/json" \
  -d '"active"'
```

### MCP Integration

Both applications expose MCP endpoints at `/mcp` for AI language model integration:

```bash
# Get MCP server info
curl http://localhost:5000/mcp

# MCP tool call (requires authentication)
curl -X POST http://localhost:5000/mcp \
  -H "Authorization: Bearer <oauth-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "add_note",
      "arguments": {"title": "Test", "content": "Hello"}
    },
    "id": 1
  }'
```

## Architecture Comparison

### Flask Demo (`application.py`)
- **Synchronous**: Traditional WSGI application
- **Templating**: Jinja2 templates with server-side rendering
- **Best for**: Traditional web applications, server-side rendering
- **Deployment**: Standard WSGI servers (Gunicorn, uWSGI)

```python
# Flask-style route handling
@app.route("/health")
def health_check():
    return {"status": "healthy"}
```

### FastAPI Demo (`fastapi_application.py`)
- **Asynchronous**: Modern ASGI application with async/await
- **API Documentation**: Automatic OpenAPI/Swagger generation
- **Type Safety**: Full Pydantic model integration
- **Best for**: API-first applications, microservices
- **Deployment**: ASGI servers (Uvicorn, Hypercorn)

```python
# FastAPI-style route handling with automatic docs
@fastapi_app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
```

## ActingWeb Hooks

Both applications use the same ActingWeb hook system:

```python
# Property hooks for access control
@app.property_hook("email")
def handle_email_property(actor, operation, value, path):
    if operation == "get":
        return None  # Hide from external access
    return value

# Method hooks for RPC-style calls
@app.method_hook("greet")
def handle_greet(actor, method_name, data):
    name = data.get("name", "World")
    return {"message": f"Hello, {name}!"}

# Action hooks for side effects
@app.action_hook("notify")
def handle_notify(actor, action_name, data):
    # Send notification
    return True

# Lifecycle hooks
@app.lifecycle_hook("actor_created")
def on_actor_created(actor, **kwargs):
    actor.properties.created_at = str(datetime.now())
```

## MCP Tools

Both applications expose the same MCP tools through the shared MCP functionality:

- `add_note`: Create a new note
- `list_notes`: List all notes with optional filtering
- `add_reminder`: Create a reminder with due date
- `list_reminders`: List pending/completed reminders
- `update_preferences`: Update user preferences

## Development

### Running Tests
```bash
# Run the test suite (if available)
python -m pytest tests/

# Or use the Runscope test collection
# Import test suites from tests/ directory into Runscope
```

### Local Development with Docker
```bash
# Start local DynamoDB
docker run -p 8000:8000 amazon/dynamodb-local

# Update environment
export AWS_ENDPOINT_URL=http://localhost:8000
export AWS_ACCESS_KEY_ID=dummy
export AWS_SECRET_ACCESS_KEY=dummy
```

## Deployment

### AWS Lambda (Serverless)
Both applications can be deployed to AWS Lambda using the Serverless framework.

### AWS Elastic Beanstalk
Deploy using the AWS EB CLI for managed hosting.

### Docker
Build production containers using the included Dockerfile.

## Production Considerations

1. **Security**: Set `with_devtest(enable=False)` in production
2. **HTTPS**: Use `proto="https://"` with proper SSL certificates
3. **Environment Variables**: Use proper secret management
4. **Database**: Configure production DynamoDB tables
5. **Monitoring**: Add logging and monitoring solutions

## License

This project is licensed under the MIT License - see the LICENSE file for details.