===============
Getting Started
===============

This actingwebdemo application is a full ActingWeb demo that uses the python
library actingweb with modern web framework integrations.

The actingweb library currently supports AWS DynamoDB and this application can be deployed to AWS
as Lambda function or run locally. There are config files for both ElasticBeanstalk and Serverless
deployment (see below).

This demo includes two different applications showcasing ActingWeb integration:

**application.py** - Flask Demo Application
   Uses the Flask framework with the modern ActingWeb interface. This demonstrates the new
   decorator-based hook system that replaces the old OnAWBase approach. All ActingWeb endpoints
   are automatically handled with clean, focused hook functions for customization.

**fastapi_application.py** - FastAPI Demo Application  
   Uses FastAPI with automatic OpenAPI documentation generation. This demonstrates the same
   ActingWeb functionality but with modern async/await support, automatic API docs at /docs,
   and the same decorator-based hook system.

Both applications include:

- **MCP Integration**: Model Context Protocol support for AI language model integration
- **OAuth2 Authentication**: Support for Google and GitHub OAuth2 providers  
- **Modern Hook System**: Decorator-based hooks instead of monolithic OnAWBase class
- **Automatic Integration**: Framework-specific integration with minimal boilerplate

The **on_aw.py** file is kept for reference but is no longer used. All functionality has been
moved to the modern decorator-based hook system in the main application files.


Extending the demo
------------------
You can modify templates in the templates directory and customize functionality using the modern
hook system. Instead of the old OnAWBase class, use decorators to add custom logic:

**Property Hooks** - Control property access and validation::

    @app.property_hook("email")
    def handle_email_property(actor, operation, value, path):
        if operation == "get":
            return None  # Hide from external access
        return value.lower() if "@" in value else None

**Method Hooks** - Add RPC-style function calls::

    @app.method_hook("calculate")
    def handle_calculate(actor, method_name, data):
        a, b = data.get("a", 0), data.get("b", 0)
        return {"result": a + b}

**Action Hooks** - Handle side effects and triggers::

    @app.action_hook("send_notification")
    def handle_notification(actor, action_name, data):
        # Send notification logic
        return True

**Lifecycle Hooks** - React to actor lifecycle events::

    @app.lifecycle_hook("actor_created")
    def on_actor_created(actor, **kwargs):
        actor.properties.created_at = str(datetime.now())

**MCP Hooks** - Expose functionality to AI language models::

    @app.mcp_tool("add_note", "Add a new note with title and content")
    @app.action_hook("add_note")
    def handle_add_note(actor, action_name, data):
        # Add note logic
        return {"status": "success"}

Running locally/Docker
----------------------

You don't have to deploy to AWS to test the app. There are multiple ways to run locally:

**Option 1: Docker Compose (Recommended)**
   There is a docker-compose.yml file that brings up both a local DynamoDB and the app::

   1. docker-compose up -d
   2. Go to http://localhost:5000

**Option 2: Direct Python Execution**
   Run either application directly with Python::

   # Flask demo
   python application.py
   
   # FastAPI demo  
   python fastapi_application.py

   Both will start on http://localhost:5000

**Option 3: Poetry (Recommended for Development)**
   Use Poetry for dependency management::

   poetry install
   poetry shell
   python application.py  # or fastapi_application.py

**FastAPI Features**
   The FastAPI demo includes automatic API documentation:
   
   - Swagger UI: http://localhost:5000/docs
   - ReDoc: http://localhost:5000/redoc

**Exposing Publicly**
   You can use ngrok.io or similar to expose the app on a public URL for testing OAuth2
   and webhooks. Remember to update the APP_HOST_FQDN environment variable.
   See start-ngrok.sh for how to start up ngrok.

Running tests
-------------
If you use ngrok.io (or deploy to AWS), you can use the Runscope tests found in the tests directory. Just sign-up at
runscope.com and import the test suites. The Basic test suite tests all actor creation and properties functionality,
while the trust suite also tests trust relationships between actors, and the subscription suite tests
subscriptions between actors with trust relationships. Thus, if basic test suite fails, all will fail, and if trust
test suite fails, subscription test suite will also fail.
The attributes test relies on the devtest endpoint to validate the internal attributes functionality to store
attributes on an actor that are not exposed through properties or any other ActingWeb endpoint.

AWS Lambda
----------
You can deploy the app to AWS Lamda in three simple steps. There is a serverless.yml file with the config you need.

1. `Install Serverless <https://serverless.com/framework/docs/providers/aws/guide/installation/>`_

2. Edit serverless.yml APP_HOST_FQDN to use your domain (or AWS domain, see 4.) and region if you prefer another

3. Run `sls deploy`

4. (if using AWS allocated domain) Use the long domain name AWS assigns the lambda and go to #2 above


AWS Elastic Beanstalk
---------------------

You can also deploy to Elastic Beanstalk:

0. Delete the config.yml in .elasticbeanstalk (it's just for your reference)

1. Install `Elastic Beanstalk CLI <http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html>`_

2. Edit .ebextensions/options.config to set the hostname you are going to deploy to, region that matches, and the
protocol (use http:// if you don't want to set up a certificate just for testing)

2. Run `eb init`, set region and AWS credentials, create a new app (your new app), and select Docker, latest version

3. Run `eb create` to create an environment (e.g. dev, prod etc of your app). Remember to match the CNAME prefix with
the prefix of the hostname in options.config (the rest is based on region)

4. Deploy with `eb deploy`

5. Run `eb open` to open the app in the browser


MCP Integration
---------------

Both applications include Model Context Protocol (MCP) integration for AI language models:

**Available MCP Tools:**
- add_note: Create a new note with title and content
- list_notes: List all notes with optional tag filtering  
- add_reminder: Create reminders with due dates
- list_reminders: List pending or completed reminders
- update_preferences: Update user preferences

**MCP Authentication:**
The /mcp endpoint requires OAuth2 Bearer token authentication. Use Google or GitHub OAuth2
to obtain access tokens.

**Example MCP Usage:**
JSON-RPC calls to /mcp endpoint::

   POST /mcp
   Authorization: Bearer <oauth-token>
   Content-Type: application/json
   
   {
     "jsonrpc": "2.0",
     "method": "tools/call", 
     "params": {
       "name": "add_note",
       "arguments": {"title": "Meeting Notes", "content": "Important discussion"}
     },
     "id": 1
   }

OAuth2 Configuration
--------------------

Both applications support Google and GitHub OAuth2 providers:

**Environment Variables:**
- OAUTH_PROVIDER: "google" or "github"
- OAUTH_CLIENT_ID: Your OAuth2 client ID
- OAUTH_CLIENT_SECRET: Your OAuth2 client secret

**Google OAuth2 Setup:**
1. Go to Google Cloud Console
2. Create OAuth2 credentials
3. Add redirect URI: http://localhost:5000/oauth/callback

**GitHub OAuth2 Setup:**  
1. Go to GitHub Settings > Developer settings
2. Create new OAuth App
3. Set callback URL: http://localhost:5000/oauth/callback

Use the library for your own projects
-------------------------------------

For how to use and extend the library, see the `ActingWeb repository <https://github.com/gregertw/actingweb>`_

The modern interface shown in these demos provides:
- 90% less boilerplate code
- Better type safety and IDE support  
- Cleaner separation of concerns
- Easier testing and maintenance
- Framework-agnostic design (Flask, FastAPI, or others)

