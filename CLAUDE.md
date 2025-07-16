# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the ActingWeb demo application that showcases the modern ActingWeb interface. It demonstrates the new fluent API and decorator-based hook system that replaces the old OnAWBase callback approach.

The application uses the new `ActingWebApp` class with automatic Flask integration, providing a clean, maintainable codebase with minimal boilerplate.

## Key Features

- **Modern Interface**: Uses `ActingWebApp` with fluent configuration API
- **Decorator-Based Hooks**: Simple, focused functions for handling events
- **Automatic Route Generation**: No manual Flask route definitions needed
- **Clean Architecture**: Separation of concerns with focused hook functions
- **Type Safety**: Better IDE support and error detection

## Development Commands

### Local Development
```bash
# Start with Docker Compose (recommended for local development)
docker-compose up -d

# Access the application at http://localhost:5000
```

### Python Dependencies
```bash
# Install dependencies using Poetry
poetry install

# Run the application directly
poetry run python application.py
```

### Testing
This project uses Runscope tests found in the `tests/` directory. To run tests:
1. Deploy the app to a publicly accessible URL (using ngrok or AWS)
2. Import the test suites from the `tests/` directory into Runscope
3. Run the test suites in order: Basic → Trust → Subscription → Attributes

## Architecture

### Core Components

**application.py** - Main application using modern interface:
- Uses `ActingWebApp` with fluent configuration
- Defines hooks using decorators (`@app.property_hook`, `@app.callback_hook`, etc.)
- Automatic Flask integration with `app.integrate_flask(flask_app)`
- No manual route definitions needed

**on_aw.py** - Legacy file kept for reference:
- Contains deprecated `OnAWDemo` class (no longer used)
- Kept for backward compatibility but not used by modern implementation
- All functionality moved to decorator-based hooks in application.py

### Modern Hook System

The application uses focused hook functions instead of a monolithic class:

#### Property Hooks
```python
@app.property_hook("email")
def handle_email_property(actor, operation, value, path):
    if operation == "get":
        return None  # Hide email from external access
    elif operation == "put":
        return value.lower() if "@" in value else None
    return value
```

#### Callback Hooks
```python
@app.callback_hook("bot")
def handle_bot_callback(actor, name, data):
    if data.get("method") == "POST":
        # Process bot request
        return True
    return False
```

#### Subscription Hooks
```python
@app.subscription_hook
def handle_subscription_callback(actor, subscription, peer_id, data):
    # Process subscription data
    return True
```

#### Lifecycle Hooks
```python
@app.lifecycle_hook("actor_created")
def on_actor_created(actor, **kwargs):
    # Initialize new actor
    actor.properties.created_at = str(datetime.now())
```

### Configuration

The modern interface uses fluent configuration:

```python
app = ActingWebApp(
    aw_type="urn:actingweb:actingweb.org:actingwebdemo",
    database="dynamodb",
    fqdn=os.getenv("APP_HOST_FQDN", "localhost:5000")
).with_oauth(
    client_id=os.getenv("APP_OAUTH_ID", ""),
    client_secret=os.getenv("APP_OAUTH_KEY", "")
).with_web_ui().with_devtest()
```

### Request Flow

1. Flask receives HTTP requests
2. ActingWeb integration automatically routes to appropriate handlers
3. Hooks are executed at appropriate points in the request lifecycle
4. Response is automatically formatted and returned

### ActingWeb Endpoints

All standard ActingWeb endpoints are automatically available:
- `/` - Actor factory (create new actors)
- `/<actor_id>` - Actor root endpoint
- `/<actor_id>/meta` - Actor metadata
- `/<actor_id>/properties` - Actor properties (key-value storage)
- `/<actor_id>/trust` - Trust relationships with other actors
- `/<actor_id>/subscriptions` - Subscription management
- `/<actor_id>/callbacks` - Callback handlers
- `/<actor_id>/resources` - Custom resources
- `/<actor_id>/www` - Web UI for actor management
- `/<actor_id>/devtest` - Development/testing endpoints
- `/oauth` - OAuth callback handling
- `/bot` - Bot integration endpoint

## Property Access Control

The demo implements property access control through hooks:

```python
PROP_HIDE = ["email"]  # Hidden from external access
PROP_PROTECT = PROP_HIDE + []  # Protected from modification/deletion
```

## Actor Management

Creating and managing actors is straightforward:

```python
# Actor creation is handled by the actor factory
@app.actor_factory
def create_actor(creator: str, **kwargs) -> ActorInterface:
    actor = ActorInterface.create(creator=creator, config=app.get_config())
    actor.properties.email = creator
    return actor

# Access actor properties
actor.properties.email = "user@example.com"
actor.properties.status = "active"

# Manage trust relationships
peer = actor.trust.create_relationship(
    peer_url="https://peer.example.com/actor123",
    relationship="friend"
)

# Handle subscriptions
actor.subscriptions.subscribe_to_peer(
    peer_id="peer123",
    target="properties"
)
```

## Deployment

### AWS Lambda (Serverless)
```bash
# Install Serverless Framework
npm install -g serverless

# Edit serverless.yml to set your domain
# Deploy to AWS Lambda
sls deploy
```

### AWS Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli

# Initialize and deploy
eb init
eb create
eb deploy
```

### Docker
The application uses Poetry for dependency management and Python 3.11 runtime. The Dockerfile creates a production-ready container.

## Environment Variables

Key environment variables:
- `APP_HOST_FQDN` - The domain where the app is hosted
- `APP_HOST_PROTOCOL` - Protocol (http:// or https://)
- `APP_OAUTH_ID` - OAuth client ID
- `APP_OAUTH_KEY` - OAuth client secret
- `APP_BOT_TOKEN` - Bot token for bot integration
- `APP_BOT_EMAIL` - Bot email
- `APP_BOT_SECRET` - Bot secret
- `APP_BOT_ADMIN_ROOM` - Bot admin room
- `LOG_LEVEL` - Logging level (DEBUG, INFO, etc.)

## Database

Uses AWS DynamoDB for storage with table prefix `demo_`. For local development, docker-compose provides a local DynamoDB instance.

## Benefits of Modern Interface

1. **90% less boilerplate code** - No manual route definitions needed
2. **Better organization** - Each hook handles one specific concern
3. **Type safety** - Better IDE support and error detection
4. **Easier testing** - Hooks can be tested independently
5. **Maintainability** - Clear separation of concerns
6. **Discoverability** - Intuitive API with method chaining

## Migration from Old Interface

This demo shows how to migrate from the old OnAWBase system:

**Old (OnAWBase)**:
```python
class OnAWDemo(on_aw.OnAWBase):
    def get_properties(self, path, data):
        # 50+ lines of complex logic
        
    def put_properties(self, path, old, new):
        # 30+ lines of validation
```

**New (Modern Interface)**:
```python
@app.property_hook("email")
def handle_email_property(actor, operation, value, path):
    if operation == "get":
        return None  # Hide email
    elif operation == "put":
        return value.lower() if "@" in value else None
    return value
```

## Templates

HTML templates in `templates/` directory provide the web UI for actor management, using Jinja2 templating with ActingWeb's built-in template variables.

The modern interface automatically provides template variables through the integration layer, maintaining compatibility with existing templates.