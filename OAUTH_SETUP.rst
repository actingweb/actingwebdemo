===============================================
OAuth2 Setup for ActingWeb (Multi-Provider)
===============================================

This guide explains how to set up OAuth2 authentication for the ActingWeb demo applications, supporting both Google and GitHub providers.

Overview
========

The ActingWeb applications now support multiple OAuth2 providers through a unified authentication system, allowing users to:

1. Authenticate with their Google or GitHub account
2. Get a Bearer token for API access
3. Access all ActingWeb endpoints using the Bearer token
4. Have an ActingWeb actor automatically created based on their email/username

Prerequisites
=============

- Choose your OAuth2 provider: **Google** or **GitHub**
- Domain or ngrok URL for your application
- Environment variables configured

Provider Options
================

Option A: Google OAuth2 (Default)
----------------------------------

- Recommended for general use
- Provides user email and profile information
- Supports refresh tokens
- Uses OpenID Connect standards

Option B: GitHub OAuth2
-----------------------

- Great for developer-focused applications
- Provides username and email (if public)
- Handles private email addresses gracefully
- No refresh token support (re-authentication required)

Step 1: Setup OAuth2 Provider
==============================

Choose **one** of the following provider setups:

1A. Google OAuth2 Setup
-----------------------

1A.1 Create a Google Cloud Project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Go to the `Google Cloud Console <https://console.cloud.google.com/>`_
2. Create a new project or select an existing one
3. Enable the Google+ API (for user profile access)

1A.2 Create OAuth2 Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Go to APIs & Services > Credentials
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Configure the OAuth consent screen:

   - Application name: "ActingWeb Demo"
   - Authorized domains: Your domain (e.g., ``your-domain.com``)
   - Scopes: Add ``../auth/userinfo.email`` and ``../auth/userinfo.profile``

4. Create OAuth 2.0 Client ID:

   - Application type: "Web application"
   - Name: "ActingWeb Client"
   - Authorized redirect URIs:
   
     - ``https://your-domain.com/oauth/callback``
     - ``https://your-ngrok-id.ngrok.io/oauth/callback`` (for development)

1A.3 Get Google Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After creating the OAuth client, you'll get:

- **Client ID**: ``123456789-abcdef.apps.googleusercontent.com``
- **Client Secret**: ``GOCSPX-your-secret-here``

1B. GitHub OAuth2 Setup
-----------------------

1B.1 Create GitHub OAuth App
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Go to `GitHub Settings > Developer settings > OAuth Apps <https://github.com/settings/applications/new>`_
2. Click "New OAuth App"
3. Fill in the application details:

   - **Application name**: "ActingWeb Demo"
   - **Homepage URL**: ``https://your-domain.com``
   - **Application description**: "ActingWeb OAuth2 Demo Application"
   - **Authorization callback URL**: ``https://your-domain.com/oauth/callback``

For development with ngrok:

- **Authorization callback URL**: ``https://your-ngrok-id.ngrok.io/oauth/callback``

1B.2 Get GitHub Credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After creating the OAuth app, you'll get:

- **Client ID**: ``Iv1.a1b2c3d4e5f6g7h8``
- **Client Secret**: ``1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t`` (click "Generate a new client secret")

1B.3 Configure App Permissions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

GitHub OAuth apps automatically request:

- ``user:email`` scope (to access user's email addresses)
- Basic profile information (username, name, avatar)

Step 2: Configure Environment Variables
=======================================

2A. For Google OAuth2
----------------------

.. code-block:: bash

    # OAuth2 provider configuration (new format)
    export OAUTH_PROVIDER="google"
    export OAUTH_CLIENT_ID="123456789-abcdef.apps.googleusercontent.com"
    export OAUTH_CLIENT_SECRET="GOCSPX-your-secret-here"

    # Application configuration
    export APP_HOST_FQDN="your-domain.com"  # or "your-ngrok-id.ngrok.io"
    export APP_HOST_PROTOCOL="https://"

    # Other required variables
    export LOG_LEVEL="INFO"

2B. For GitHub OAuth2
----------------------

.. code-block:: bash

    # OAuth2 provider configuration (new format)
    export OAUTH_PROVIDER="github"
    export OAUTH_CLIENT_ID="Iv1.a1b2c3d4e5f6g7h8"
    export OAUTH_CLIENT_SECRET="1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t"

    # Application configuration
    export APP_HOST_FQDN="your-domain.com"  # or "your-ngrok-id.ngrok.io"
    export APP_HOST_PROTOCOL="https://"

    # Other required variables
    export LOG_LEVEL="INFO"

2C. Legacy Environment Variables (Backward Compatible)
-------------------------------------------------------

The applications also support legacy environment variable names:

.. code-block:: bash

    # Legacy Google OAuth2 (still supported)
    export GOOGLE_OAUTH_CLIENT_ID="123456789-abcdef.apps.googleusercontent.com"
    export GOOGLE_OAUTH_CLIENT_SECRET="GOCSPX-your-secret-here"

    # Legacy general OAuth2 (still supported)
    export APP_OAUTH_ID="your-client-id"
    export APP_OAUTH_KEY="your-client-secret"

Development with ngrok:

.. code-block:: bash

    # Start ngrok
    ngrok http 5000

    # Use the ngrok URL
    export APP_HOST_FQDN="abc123.ngrok.io"
    export APP_HOST_PROTOCOL="https://"

Step 3: Authentication Flow
===========================

3.1 Client Authentication
--------------------------

When a client accesses a protected endpoint without authentication:

.. code-block:: bash

    curl -X GET https://your-domain.com/mcp

Response:

.. code-block:: json

    {
      "error": true,
      "status_code": 401,
      "message": "Authentication required"
    }

Headers (dynamically generated based on configured provider):

.. code-block:: text

    # For Google OAuth2
    WWW-Authenticate: Bearer realm="ActingWeb", authorization_uri="https://accounts.google.com/o/oauth2/v2/auth?client_id=..."

    # For GitHub OAuth2  
    WWW-Authenticate: Bearer realm="ActingWeb", authorization_uri="https://github.com/login/oauth/authorize?client_id=..."

3.2 User Authorization
----------------------

1. Client extracts the ``authorization_uri`` from the WWW-Authenticate header
2. Client redirects user to the configured OAuth2 provider (Google or GitHub) for authentication
3. User grants permission to the application
4. Provider redirects back to ``/oauth/callback`` with authorization code

3.3 Token Exchange
-------------------

The callback endpoint automatically handles both providers:

For Google OAuth2:
~~~~~~~~~~~~~~~~~~~

1. Exchanges authorization code for access token (with refresh token)
2. Validates token with Google's userinfo API
3. Extracts user email from Google profile
4. Looks up existing actor or creates new one based on email
5. Returns success response with Bearer token

For GitHub OAuth2:
~~~~~~~~~~~~~~~~~~~

1. Exchanges authorization code for access token (no refresh token)
2. Validates token with GitHub's user API
3. Extracts user email (or uses username@github.local if email is private)
4. Looks up existing actor or creates new one based on email/username
5. Returns success response with Bearer token

3.4 API Access
---------------

Client uses the Bearer token for subsequent requests:

.. code-block:: bash

    curl -X POST https://your-domain.com/mcp \
      -H "Authorization: Bearer ya29.a0AfH6SMC..." \
      -H "Content-Type: application/json" \
      -d '{"method": "initialize", "id": 1}'

Step 4: Testing the Setup
=========================

4.1 Check Configuration
------------------------

Visit the MCP info endpoint:

.. code-block:: bash

    curl https://your-domain.com/mcp/info

Should return (example for Google):

.. code-block:: json

    {
      "mcp_enabled": true,
      "authentication": {
        "type": "oauth2",
        "provider": "google",
        "enabled": true,
        "callback_url": "https://your-domain.com/oauth/callback",
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "scopes": ["openid", "email", "profile"]
      }
    }

Or for GitHub:

.. code-block:: json

    {
      "mcp_enabled": true,
      "authentication": {
        "type": "oauth2", 
        "provider": "github",
        "enabled": true,
        "callback_url": "https://your-domain.com/oauth/callback",
        "auth_url": "https://github.com/login/oauth/authorize",
        "scopes": ["user:email"]
      }
    }

4.2 Test Authentication Flow
-----------------------------

1. Access MCP endpoint without token:

   .. code-block:: bash

       curl -i https://your-domain.com/mcp

2. Look for WWW-Authenticate header with OAuth2 provider auth URL

3. Open the auth URL in browser and complete OAuth2 provider sign-in (Google or GitHub)

4. Verify redirect to ``/oauth/callback`` succeeds

5. Use returned Bearer token for API access

Step 5: Actor Management
========================

5.1 Actor Creation
------------------

Actors are automatically created based on OAuth2 provider identity:

For Google OAuth2:
~~~~~~~~~~~~~~~~~~~

- Actor ID: Generated unique identifier
- Creator: User's Google email address  
- Properties: Include email, auth method (``google_oauth2``), creation timestamp

For GitHub OAuth2:
~~~~~~~~~~~~~~~~~~~

- Actor ID: Generated unique identifier
- Creator: User's GitHub email or ``username@github.local`` (if email is private)
- Properties: Include email/username, auth method (``github_oauth2``), creation timestamp

5.2 Actor Lookup
-----------------

Subsequent authentications will:

1. Validate the Bearer token with the OAuth2 provider
2. Extract user identity (email from Google, email/username from GitHub)
3. Find existing actor by creator identity
4. Return the same actor instance

5.3 Data Persistence
---------------------

Each user's data (notes, reminders, etc.) is stored per-actor:

- Notes created via MCP tools are stored in ``actor.properties.notes``
- Reminders are stored in ``actor.properties.reminders``
- Usage statistics tracked in ``actor.properties.mcp_usage_count``

Step 6: Security Considerations
===============================

6.1 Token Validation
---------------------

Every Bearer token is validated with the OAuth2 provider on each request:

- Prevents use of expired tokens
- Ensures token wasn't revoked
- Confirms token belongs to expected user

6.2 HTTPS Required
------------------

OAuth2 requires HTTPS in production:

- Google and GitHub only allow HTTPS redirect URIs
- Bearer tokens must be transmitted securely
- Use proper TLS certificates

6.3 Scope Limitations
----------------------

The application requests minimal scopes per provider:

Google OAuth2:
~~~~~~~~~~~~~~

- ``openid``: Basic authentication
- ``email``: To identify the user
- ``profile``: For user display name (optional)

GitHub OAuth2:
~~~~~~~~~~~~~~

- ``user:email``: To access user's email addresses (including private emails)

6.4 Actor Isolation
--------------------

Each actor's data is completely isolated:

- No cross-actor data access
- Identity-based actor lookup prevents account takeover
- Properties are scoped to individual actors
- Different OAuth2 providers create separate actor namespaces

Troubleshooting
===============

Common Issues
-------------

1. **"OAuth2 not configured" error**

   - Check ``OAUTH_CLIENT_ID`` and ``OAUTH_CLIENT_SECRET`` are set
   - Or check legacy ``GOOGLE_OAUTH_CLIENT_ID``/``GOOGLE_OAUTH_CLIENT_SECRET`` or ``APP_OAUTH_ID``/``APP_OAUTH_KEY``
   - Verify environment variables are exported correctly
   - Ensure ``OAUTH_PROVIDER`` is set to "google" or "github"

2. **"Redirect URI mismatch" error**

   - Ensure redirect URI in OAuth provider console matches your domain
   - For Google: Check Google Cloud Console OAuth2 credentials
   - For GitHub: Check GitHub OAuth App settings
   - Verify ``APP_HOST_FQDN`` and ``APP_HOST_PROTOCOL`` are correct

3. **"Token validation failed" error**

   - **For Google**: Verify Google+ API is enabled in Google Cloud Console
   - **For GitHub**: Check that User-Agent headers are properly set
   - Check token hasn't expired (GitHub tokens don't have refresh tokens)
   - Ensure proper scopes were granted during authorization

4. **"Actor creation failed" error**

   - Check database connectivity (DynamoDB)
   - Verify ActingWeb configuration is valid
   - Look for database permission issues
   - Check if unique creator constraint is causing conflicts

5. **"GitHub email not found" errors**

   - GitHub user may have private email settings
   - Application will automatically use ``username@github.local`` as fallback
   - Check that ``user:email`` scope is properly requested and granted

Debug Logging
-------------

Enable debug logging:

.. code-block:: bash

    export LOG_LEVEL="DEBUG"

This will log:

- OAuth2 authentication attempts
- Token validation steps
- Actor lookup/creation process
- API request details

Integration with ChatGPT and MCP Clients
=========================================

To use with ChatGPT's MCP support or other MCP clients:

1. Configure the MCP server URL: ``https://your-domain.com/mcp``
2. MCP client will handle the OAuth2 flow automatically
3. Users will be prompted to authenticate with their chosen OAuth2 provider (Google or GitHub)
4. Once authenticated, the MCP client can use all available tools and prompts
5. Each user gets their own isolated actor and data based on their OAuth2 identity

Supported MCP Features
----------------------

The integration supports:

- **Tools**: ``search``, ``fetch``, ``create_note``, ``create_reminder``
- **Prompts**: ``analyze_notes``, ``create_learning_prompt``, ``create_meeting_prep``
- **Resources**: Access to notes, reminders, and usage statistics

Provider-Specific Behavior
---------------------------

Google OAuth2 + MCP:
~~~~~~~~~~~~~~~~~~~~

- Users authenticate with Google accounts
- Email-based actor identification
- Long-lived sessions with refresh token support

GitHub OAuth2 + MCP:
~~~~~~~~~~~~~~~~~~~~

- Users authenticate with GitHub accounts  
- Username or email-based actor identification
- Handles private GitHub email addresses gracefully
- No refresh tokens (users re-authenticate when tokens expire)

Multi-User Support
-------------------

Each OAuth2 provider creates separate user namespaces:

- Google user ``alice@gmail.com`` and GitHub user ``alice`` are different actors
- Data is completely isolated between providers and users
- MCP clients can support users from multiple OAuth2 providers simultaneously