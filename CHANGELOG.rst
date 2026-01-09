=========
CHANGELOG
=========

[Jan 9, 2026]
------------

Fixed
~~~~~

- **Property Deletion Subscription Callbacks**: Fixed subscription callbacks not being triggered when deleting properties via web UI by migrating from ``?_method=DELETE`` to proper HTTP DELETE requests with JavaScript fetch API

[Jan 3, 2026]
------------

Changed
~~~~~~~

- **ActingWeb Library**: Updated to v3.8.2 for latest fixes and improvements

Fixed
~~~~~

- **Nuke Endpoint Environment Support**: Fixed nuke endpoint to respect AWS_DB_HOST and AWS_DB_PREFIX environment variables
  - Now properly connects to local DynamoDB when AWS_DB_HOST is set
  - Dynamically uses table prefix from AWS_DB_PREFIX (defaults to "demo_actingweb")
  - Ensures consistent database configuration with ActingWeb core

[Jan 2, 2026]
------------

Added
~~~~~

- **Trust Lifecycle Hooks**: Added ``trust_hooks.py`` module with lifecycle hooks for trust relationship events
  - ``trust_approved`` hook: Triggered when both parties approve a trust relationship
  - ``trust_deleted`` hook: Triggered before a trust relationship is deleted
  - Provides logging and extension points for custom trust management workflows

Changed
~~~~~~~

- **Trust Auto-Approval**: Enabled automatic approval for "friend" trust relationships
  - Set ``default_relationship`` to "friend" to match configured actor types
  - Set ``auto_accept_default_relationship`` to ``True`` for automatic approval
  - Other relationship types (subscriber, admin, associate) require manual approval

Fixed
~~~~~

- **Trust Approve Button**: Fixed parameter name mismatch preventing trust approval in web UI
  - Changed template parameter from ``approve=true`` to ``approved=true``
  - Approve button now correctly approves pending trust relationships

[Dec 26, 2025]
------------

Added
~~~~~

- **Nuke Endpoint**: New ``GET /nuke?secret=<NUKE_SECRET>`` endpoint for test environment cleanup
  - Deletes all actors and their associated data from DynamoDB
  - Requires ``NUKE_SECRET`` environment variable for authorization
  - Preserves system actors (``_actingweb_*``)
  - Returns detailed JSON report of deleted/skipped/errored actors
- **Serverless Dotenv Plugin**: Added ``serverless-dotenv-plugin`` for automatic ``.env`` loading during deployment

Changed
~~~~~~~

- **Environment Configuration**: Added ``NUKE_SECRET`` environment variable to serverless.yml
- **Dotenv Exclusions**: Configured dotenv plugin to exclude AWS reserved variables from Lambda deployment

[Dec 19, 2025]
--------------

**Full Refactoring Update with MCP Support**

Breaking
~~~~~~~~

- **OAuth2 Configuration Changes**: OAuth2 is now enabled by default with Google as the provider
- **Actor Creation Policy**: Unique creator and email-as-creator are now enabled by default

Added
~~~~~

- **MCP Server Support**: Added Model Context Protocol server integration for AI language models
  - New ``search`` MCP tool to search across actor properties by keyword
  - ``mcp_client`` trust type with read-only access and sensitive data exclusion
  - Excludes email, auth_token, oauth_token, access_token, refresh_token from MCP access
  - Safety annotations for tool behavior (readOnlyHint, destructiveHint)
- **API Explorer**: New web UI page at ``/{actor_id}/www/demo`` for testing hooks interactively
  - Test methods, actions, and callbacks from the browser
  - Real-time JSON response display
  - Organized by hook type with input forms
- **Comprehensive Hook Documentation**: All shared_hooks files now include detailed docstrings
  - Endpoint paths, parameters, return values documented for each hook
  - Module-level documentation with usage examples
- **New Method Hooks**: Added ``echo`` method for testing
- **Environment Support**: Added python-dotenv for loading .env files
- **OAuth2 State Manager**: Pre-initialized OAuth2 state manager for MCP OAuth flows
- **Development Tools**: Added ruff and pyright to dev dependencies for code quality

Changed
~~~~~~~

- **ActingWeb Library**: Updated to v3.7.2 (includes Flask auth fix)
- **MCP Enabled**: Application now has ``.with_mcp(enable=True)`` for MCP protocol support
- **UI Templates Redesign**: Completely modernized all HTML templates with:
  - Modern responsive design using Inter font family
  - Consistent card-based layout across all pages
  - SVG icons throughout the interface
  - Improved accessibility and mobile support
  - New dashboard, properties, trust, and OAuth authorization views
- **CSS Overhaul**: Major expansion of style.css with modern design system
- **Proxy Fix Middleware**: Added Werkzeug ProxyFix for proper header handling
- **Hook Improvements**: Refined shared hooks for better error handling

Aug 5, 2025
-----------

**Modular Architecture Update**

- **Shared Hooks**: Created shared_hooks/ directory for reusable hook implementations
- **ActingWeb Library**: Updated to actingweb v3.2 for latest features and improvements

Jul 14, 2025
------------

**ActingWeb Library Compatibility Update**

- **Library Compatibility**: Updated codebase to work with refactored actingweb library v3.0+
- **Type System Improvements**:
  - Updated on_aw.py method signatures to accept Union[dict, str] parameters as required by new actingweb types
  - Added proper typing imports and modernized type annotations using Optional[dict] syntax
  - Fixed property methods (get_properties, put_properties, post_properties) to handle both dict and string data
- **Handler Method Fixes**:
  - Updated application.py Handler.process() method to use dynamic method access with getattr()
  - Fixed missing HTTP method attributes (post, get, delete, put) in actingweb handlers
  - Improved error handling for handlers that don't implement all HTTP methods
- **Flask Route Improvements**:
  - Fixed potential None return values in Flask route functions
  - Ensured all routes return valid Flask Response objects
- **Data Processing Enhancements**:
  - Added JSON string parsing for property data in both put_properties and post_properties
  - Added type guards to ensure proper data validation
  - Fixed devtest/proxy/properties endpoint handling for single property scenarios
- **Code Quality**:
  - Resolved all Pylance type checking errors
  - Commented out unused gmail functionality to prevent import errors
  - Maintained backward compatibility with existing ActingWeb features

Jul 11, 2025
------------

**Major Modernization Update**

- **Python Runtime Upgrade**: Upgraded from Python 3.7 to Python 3.11 for AWS Lambda compatibility
- **Dependency Management**: Migrated from Pipenv to Poetry for better dependency resolution and modern tooling
- **Framework Updates**:
  - Updated Flask from 1.1.2 to 3.1.1 with modern features and security fixes
  - Updated Jinja2 from 2.11.3 to 3.1.6 for improved template processing
  - Updated uWSGI from 2.0.19.1 to 2.0.30 for better performance
  - Updated Werkzeug to 3.1.3 for latest Flask compatibility
- **Infrastructure Modernization**:
  - Upgraded Serverless Framework to v4.17.1 with modern deployment features
  - Updated serverless-wsgi plugin from 1.7.8 to 3.1.0 for Flask 3.x compatibility
  - Updated serverless-python-requirements plugin to v6.1.2 with Poetry support
- **Docker Updates**:
  - Updated Docker base image from python:3.7-slim-buster to python:3.11-slim-bookworm
  - Refactored Dockerfile to use Poetry instead of Pipenv
  - Improved build process with Poetry configuration
- **Configuration Changes**:
  - Created pyproject.toml with modern Python project configuration
  - Updated serverless.yml with Poetry integration and optimized settings
  - Adjusted Lambda timeout from 30s to 29s to match API Gateway limits
  - Added Docker-based dependency packaging for better compatibility
- **Development Environment**:
  - Added poetry.lock file for reproducible builds
  - Updated requirements.txt generation via Poetry export
  - Removed legacy Pipfile and Pipfile.lock files
  - Updated CLAUDE.md with Poetry-based development instructions
- **Compatibility Fixes**:
  - Maintained full backward compatibility - no functional changes to ActingWeb features

Aug 22, 2020
-------------

- Put on_aw.py in src/
- Add code to show how the app can authenticate against Google to access Google services
- Fix issue where 403 Forbidden was not correctly returned
- Upgrade serverless dependencies
- Upgrade to python3.7
- Added warning on AWS API Gateway not allowing login on www
- Improve templates

Nov 21, 2018
------------

- Update to use actingweb v2.5.0

Oct 22, 2018
------------

- Updated to use python3, lambda, and dynamodb
- Deployed to https://demo.actingweb.io


Nov 12, 2017
------------

- Forked as separate demo app from actingweb library
- Deployed to https://actingwebdemo.greger.io as a test app


