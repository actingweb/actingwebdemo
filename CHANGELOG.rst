=========
CHANGELOG
=========

Aug 5, 2025
-----------

**MCP Server Integration**

- **MCP Server Support**: Added complete Model Context Protocol (MCP) server implementation for AI language model integration
- **FastAPI Application**: Created new fastapi_application.py with modern async/await support and automatic OpenAPI documentation
- **Dual Framework Support**: Now supports both Flask (application.py) and FastAPI (fastapi_application.py) implementations
- **AI Tool Integration**:
  - Added MCP tools for actor management, property operations, and trust relationship handling
  - Implemented search functionality across actor data
  - Created shared MCP modules in shared_mcp/ directory for reusable functionality
- **Configuration**: Added mcp-config.json for MCP server configuration and client integration
- **Modular Architecture**:
  - Created shared_hooks/ directory for reusable hook implementations
  - Separated MCP-specific logic into shared_mcp/ modules (tools.py, prompts.py, helpers.py)
  - Maintained compatibility with existing Flask-based implementation
- **ActingWeb Library**: Updated to actingweb v3.2 for latest features and improvements
- **Development Tools**: Enhanced development workflow with dual framework support and MCP integration

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


