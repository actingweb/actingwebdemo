# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ActingWeb demo application built with Python Flask and the ActingWeb framework. ActingWeb is a protocol for creating distributed actor-based systems where actors can communicate via standardized REST APIs. This demo showcases the core ActingWeb capabilities including actor creation, properties, trust relationships, and subscriptions.

## Development Commands

### Local Development
```bash
# Start with Docker Compose (recommended for local development)
docker-compose up -d

# Access the application at http://localhost:5000
```

### Python Dependencies
```bash
# Install dependencies using pipenv
pipenv install --dev

# Run the application directly (without Docker)
python application.py
```

### Testing
This project uses Runscope tests found in the `tests/` directory. To run tests:
1. Deploy the app to a publicly accessible URL (using ngrok or AWS)
2. Import the test suites from the `tests/` directory into Runscope
3. Run the test suites in order: Basic → Trust → Subscription → Attributes

## Architecture

### Core Components

**application.py** - Main Flask application that:
- Maps all ActingWeb endpoints to Flask routes
- Uses `SimplifyRequest` class to normalize Flask requests for ActingWeb
- Uses `Handler` class to process ActingWeb responses back to Flask
- Implements the complete ActingWeb actor lifecycle

**on_aw.py** - Application-specific logic extending `on_aw.OnAWBase`:
- Handles property access controls via `PROP_HIDE` and `PROP_PROTECT`
- Implements callback handlers for bot, oauth, subscriptions, and resources
- Provides hooks for customizing ActingWeb behavior

### Request Flow
1. Flask routes capture HTTP requests
2. `Handler` class determines the appropriate ActingWeb handler
3. `SimplifyRequest` normalizes the Flask request
4. ActingWeb framework processes the request
5. Response is converted back to Flask format

### ActingWeb Endpoints
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
The application uses Alpine Linux with uWSGI for production deployment. The Dockerfile creates a production-ready container with proper user permissions and web server configuration.

## Configuration

Key environment variables:
- `APP_HOST_FQDN` - The domain where the app is hosted
- `APP_HOST_PROTOCOL` - Protocol (http:// or https://)
- `LOG_LEVEL` - Logging level (DEBUG, INFO, etc.)
- `AWS_*` - AWS credentials and DynamoDB configuration

## Database

Uses AWS DynamoDB for storage with table prefix `demo_`. For local development, docker-compose provides a local DynamoDB instance.

## Templates

HTML templates in `templates/` directory provide the web UI for actor management, using Jinja2 templating with ActingWeb's built-in template variables.