===============
Getting Started
===============

This actingwebdemo application is a full ActingWeb demo that uses the python
library actingweb with modern web framework integrations.

The actingweb library currently supports AWS DynamoDB and this application can be deployed to AWS
as Lambda function or run locally. There are config files for both ElasticBeanstalk and Serverless
deployment (see below).

**application.py** - Flask Demo Application
   Uses the Flask framework with the modern ActingWeb interface. This demonstrates the new
   decorator-based hook system that replaces the old OnAWBase approach. All ActingWeb endpoints
   are automatically handled with clean, focused hook functions for customization.

The application includes:

- **MCP Integration**: Model Context Protocol support for AI language model integration
- **OAuth2 Authentication**: Support for Google and GitHub OAuth2 providers
- **Modern Hook System**: Decorator-based hooks instead of monolithic OnAWBase class
- **API Explorer**: Web UI for testing hooks interactively at ``/{actor_id}/www/demo``
- **Automatic Integration**: Framework-specific integration with minimal boilerplate
- **Modern Web UI**: Redesigned templates with responsive design

The **on_aw.py** file is kept for reference but is no longer used. All functionality has been
moved to the modern decorator-based hook system in application.py and shared_hooks/.


Hook System Overview
--------------------

The demo implements four types of hooks that illustrate different aspects of the ActingWeb protocol:

**Methods** - Read-only RPC-style operations (``POST /{actor_id}/methods/{name}``)

**Actions** - State-modifying operations (``POST /{actor_id}/actions/{name}``)

**Callbacks** - External integration endpoints (``POST /{actor_id}/callbacks/{name}``)

**Property Hooks** - Intercept property operations (automatic on property access)

**Lifecycle Hooks** - React to actor events (automatic, not directly callable)


Methods (Read-Only)
~~~~~~~~~~~~~~~~~~~

Methods compute and return results without modifying state. They're like pure functions.

**Endpoint**: ``POST /{actor_id}/methods/{method_name}``

Available methods:

- **calculate**: Arithmetic operations (add, subtract, multiply, divide)::

    curl -X POST https://host/{actor_id}/methods/calculate \
         -H "Content-Type: application/json" \
         -d '{"a": 10, "b": 5, "operation": "multiply"}'
    # Returns: {"result": 50, "operation": "multiply", "a": 10, "b": 5}

- **greet**: Personalized greeting with actor info::

    curl -X POST https://host/{actor_id}/methods/greet \
         -H "Content-Type: application/json" \
         -d '{"name": "Alice"}'
    # Returns: {"greeting": "Hello, Alice! This is actor abc123 via Flask.", ...}

- **get_status**: Actor status summary (property counts, relationships)::

    curl -X POST https://host/{actor_id}/methods/get_status \
         -H "Content-Type: application/json" \
         -d '{}'
    # Returns: {actor_id, creator, status, properties_count, trust_relationships, subscriptions}

- **echo**: Echo back input data (useful for testing)::

    curl -X POST https://host/{actor_id}/methods/echo \
         -H "Content-Type: application/json" \
         -d '{"test": "data"}'


Actions (State-Modifying)
~~~~~~~~~~~~~~~~~~~~~~~~~

Actions can modify actor state and trigger side effects.

**Endpoint**: ``POST /{actor_id}/actions/{action_name}``

Available actions:

- **log_message**: Log a message at specified level::

    curl -X POST https://host/{actor_id}/actions/log_message \
         -H "Content-Type: application/json" \
         -d '{"message": "Hello from action", "level": "info"}'

- **update_status**: Update actor's status property::

    curl -X POST https://host/{actor_id}/actions/update_status \
         -H "Content-Type: application/json" \
         -d '{"status": "active"}'

- **send_notification**: Simulate sending a notification::

    curl -X POST https://host/{actor_id}/actions/send_notification \
         -H "Content-Type: application/json" \
         -d '{"recipient": "user@example.com", "message": "Hello", "type": "email"}'

- **notify**: Store notification in actor properties::

    curl -X POST https://host/{actor_id}/actions/notify \
         -H "Content-Type: application/json" \
         -d '{"message": "Important notification"}'

- **search** (MCP Tool): Search actor properties::

    curl -X POST https://host/{actor_id}/actions/search \
         -H "Content-Type: application/json" \
         -d '{"query": "*", "limit": 20}'
    # Use "*" to list all properties


Callbacks (External Integration)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Callbacks provide endpoints for external systems to communicate with actors.

**Endpoint**: ``POST /{actor_id}/callbacks/{callback_name}``

Available callbacks:

- **ping**: Health check, returns "pong"::

    curl -X POST https://host/{actor_id}/callbacks/ping \
         -H "Content-Type: application/json" \
         -d '{"timestamp": "2024-01-01T00:00:00Z"}'

- **echo**: Echo back received data::

    curl -X POST https://host/{actor_id}/callbacks/echo \
         -H "Content-Type: application/json" \
         -d '{"any": "data"}'

- **status**: Return actor status (requires method: "GET" in body)

- **resource_demo**: Demo resource with GET/POST support


Property Hooks
~~~~~~~~~~~~~~

Property hooks intercept property operations and allow for access control, validation,
and transformation. They're triggered automatically on property access.

Implemented behaviors:

- **email property**: Hidden from GET, validated on PUT/POST, protected from deletion
- **Wildcard (*) hook**: JSON parsing, protection rules for sensitive properties

Protected properties (cannot be deleted): email, auth_token, created_at, actor_type


Lifecycle Hooks
~~~~~~~~~~~~~~~

Lifecycle hooks react to actor events automatically - they cannot be called directly.

- **actor_created**: Sets initial properties (demo_version, interface_version, created_at)
- **actor_deleted**: Cleanup before deletion (logging)
- **oauth_success**: Records OAuth timestamp


API Explorer
------------

The demo includes a web-based API Explorer for testing hooks interactively.
Access it at: ``https://host/{actor_id}/www/demo``

Features:

- Test all methods, actions, and callbacks from your browser
- See JSON responses in real-time
- Organized by hook type (Methods, Actions, Callbacks)


MCP Integration
---------------

This demo includes Model Context Protocol (MCP) server support, allowing AI assistants like
Claude to interact with actor data.

**Available MCP Tools:**

- **search**: Search across actor properties by keyword. Returns matching property names and
  values. Sensitive properties (email, tokens) are automatically excluded from results.

**MCP Trust Type:**

The application configures an ``mcp_client`` trust type that provides:

- Read-only access to actor properties
- Automatic exclusion of sensitive data (email, auth_token, oauth_token, access_token, refresh_token)
- Access to the search tool only
- No write operations allowed

**Testing MCP:**

After starting the application, you can test MCP functionality::

    # Initialize MCP connection
    curl -X POST http://localhost:5000/mcp \
      -H 'Content-Type: application/json' \
      -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"clientInfo":{"name":"test"}}}'

    # List available tools
    curl -X POST http://localhost:5000/mcp \
      -H 'Content-Type: application/json' \
      -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'


Adding Custom Hooks
-------------------

To add your own hooks, edit the files in ``shared_hooks/``:

**Add a new method** (shared_hooks/method_hooks.py)::

    @app.method_hook("my_method")
    def handle_my_method(actor, method_name, data):
        return {"result": "computed value"}

**Add a new action** (shared_hooks/action_hooks.py)::

    @app.action_hook("my_action")
    def handle_my_action(actor, action_name, data):
        actor.properties.something = data.get("value")
        return {"status": "done"}

**Add a property hook** (shared_hooks/property_hooks.py)::

    @app.property_hook("my_property")
    def handle_my_property(actor, operation, value, path):
        if operation == "get":
            return value.upper()  # Transform on read
        return value

**Add an MCP tool** (shared_hooks/action_hooks.py)::

    from actingweb.mcp import mcp_tool

    @app.action_hook("my_tool")
    @mcp_tool(
        description="Description for AI assistants",
        input_schema={...},
        annotations={"readOnlyHint": True}
    )
    def handle_my_tool(actor, action_name, data):
        return {"result": "for AI"}


Running locally/Docker
----------------------

You don't have to deploy to AWS to test the app. There are multiple ways to run locally:

**Option 1: Docker Compose (Recommended)**
   There is a docker-compose.yml file that brings up both a local DynamoDB and the app::

   1. docker-compose up -d
   2. Go to http://localhost:5000

**Option 2: Direct Python Execution**
   Run the application directly with Python::

   python application.py

   The app will start on http://localhost:5000

**Option 3: Poetry (Recommended for Development)**
   Use Poetry for dependency management::

   poetry install
   poetry shell
   python application.py

**Exposing Publicly**
   You can use ngrok.io or similar to expose the app on a public URL for testing OAuth2
   and webhooks. Remember to update the APP_HOST_FQDN environment variable.
   See start-ngrok.sh for how to start up ngrok.


Running tests
-------------
If you use ngrok.io (or deploy to AWS), you can use the Runscope tests found in the tests directory.
Just sign-up at runscope.com and import the test suites. The Basic test suite tests all actor creation
and properties functionality, while the trust suite also tests trust relationships between actors,
and the subscription suite tests subscriptions between actors with trust relationships.
Thus, if basic test suite fails, all will fail, and if trust test suite fails, subscription test suite
will also fail. The attributes test relies on the devtest endpoint to validate the internal attributes
functionality to store attributes on an actor that are not exposed through properties or any other
ActingWeb endpoint.


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


OAuth2 Configuration
--------------------

The application supports Google and GitHub OAuth2 providers:

**Environment Variables:**

- OAUTH_PROVIDER: "google" or "github"
- OAUTH_CLIENT_ID: Your OAuth2 client ID (also APP_OAUTH_ID)
- OAUTH_CLIENT_SECRET: Your OAuth2 client secret (also APP_OAUTH_KEY)
- OAUTH_SCOPE: OAuth scopes (defaults to "openid email profile" for Google)
- OAUTH_AUTH_URI: Authorization endpoint
- OAUTH_TOKEN_URI: Token endpoint

**Google OAuth2 Setup:**

1. Go to Google Cloud Console
2. Create OAuth2 credentials
3. Add redirect URI: https://your-domain/oauth/callback

**GitHub OAuth2 Setup:**

1. Go to GitHub Settings > Developer settings
2. Create new OAuth App
3. Set callback URL: https://your-domain/oauth/callback


Use the library for your own projects
-------------------------------------

For how to use and extend the library, see the `ActingWeb repository <https://github.com/gregertw/actingweb>`_

The modern interface shown in this demo provides:

- 90% less boilerplate code
- Better type safety and IDE support
- Cleaner separation of concerns
- Easier testing and maintenance
- Framework-agnostic design (Flask or FastAPI)
- MCP integration for AI assistants
