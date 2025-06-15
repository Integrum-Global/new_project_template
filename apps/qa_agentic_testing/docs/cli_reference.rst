CLI Reference
=============

The QA Agentic Testing framework provides a comprehensive command-line interface for testing applications, managing personas, and configuring models.

Main Commands
-------------

qa-test
~~~~~~~

The primary command for testing applications.

.. code-block:: bash

   qa-test [OPTIONS] APP_PATH

**Arguments:**

* ``APP_PATH``: Path to the application to test (required)

**Options:**

* ``--name, -n TEXT``: Project name (defaults to app directory name)
* ``--description, -d TEXT``: Project description
* ``--interfaces [cli|web|api|mobile]``: Interface types to test (multiple allowed)
* ``--test-types [functional|security|performance|usability|integration]``: Test types to include (multiple allowed)
* ``--output, -o PATH``: Output directory for reports (defaults to target app's qa_results folder)
* ``--format [html|json|both]``: Report format (default: html)
* ``--industry [financial_services|healthcare|manufacturing|retail_ecommerce]``: Load industry-specific personas
* ``--personas PATH``: Custom personas JSON file
* ``--async``: Use async performance mode (3-5x faster)
* ``--discover-personas``: Auto-generate personas from app analysis
* ``--model-preset [development|balanced|enterprise]``: Model selection preset (default: balanced)
* ``--security-model TEXT``: Specific model for security analysis (e.g., openai/gpt-4)
* ``--functional-model TEXT``: Specific model for functional testing (e.g., ollama/llama3.1:8b)
* ``--performance-model TEXT``: Specific model for performance analysis (e.g., anthropic/claude-3-sonnet)

**Examples:**

.. code-block:: bash

   # Basic testing
   qa-test /path/to/your/app

   # With healthcare personas and async performance
   qa-test /path/to/your/app --industry healthcare --async

   # Enterprise security-focused testing
   qa-test /path/to/your/app --model-preset enterprise --security-model openai/gpt-4

   # Custom configuration
   qa-test /path/to/your/app \
     --name "Production Validation" \
     --interfaces cli web api \
     --test-types functional security performance \
     --format both \
     --output ./custom-reports

Project Management
------------------

qa-test project
~~~~~~~~~~~~~~~

Manage test projects for ongoing development.

**Subcommands:**

create
^^^^^^

Create a new test project.

.. code-block:: bash

   qa-test project create [OPTIONS] NAME APP_PATH

**Arguments:**

* ``NAME``: Project name
* ``APP_PATH``: Path to the application

**Options:**

* ``--description, -d TEXT``: Project description

**Example:**

.. code-block:: bash

   qa-test project create "UserMgmt" /path/to/apps/user_management

list
^^^^

List all test projects.

.. code-block:: bash

   qa-test project list [OPTIONS]

**Options:**

* ``--format [table|json]``: Output format (default: table)

**Example:**

.. code-block:: bash

   qa-test project list

delete
^^^^^^

Delete a test project.

.. code-block:: bash

   qa-test project delete [OPTIONS] PROJECT_ID

**Arguments:**

* ``PROJECT_ID``: ID of the project to delete

**Options:**

* ``--yes``: Skip confirmation prompt

**Example:**

.. code-block:: bash

   qa-test project delete proj_123456

test
^^^^

Run tests on an existing project.

.. code-block:: bash

   qa-test project test [OPTIONS] PROJECT_ID

**Arguments:**

* ``PROJECT_ID``: ID of the project to test

**Options:**

* ``--async``: Use async performance mode
* ``--model-preset [development|balanced|enterprise]``: Model selection preset

**Example:**

.. code-block:: bash

   qa-test project test proj_123456 --async

Test Run Management
-------------------

qa-test run
~~~~~~~~~~~

Manage individual test runs.

**Subcommands:**

list
^^^^

List test runs.

.. code-block:: bash

   qa-test run list [OPTIONS]

**Options:**

* ``--project-id TEXT``: Filter by project ID
* ``--limit INTEGER``: Maximum number of runs to show (default: 20)
* ``--format [table|json]``: Output format (default: table)

**Example:**

.. code-block:: bash

   qa-test run list --project-id proj_123456 --limit 10

status
^^^^^^

Get status of a test run.

.. code-block:: bash

   qa-test run status [OPTIONS] RUN_ID

**Arguments:**

* ``RUN_ID``: ID of the test run

**Example:**

.. code-block:: bash

   qa-test run status run_789012

logs
^^^^

View logs of a test run.

.. code-block:: bash

   qa-test run logs [OPTIONS] RUN_ID

**Arguments:**

* ``RUN_ID``: ID of the test run

**Options:**

* ``--follow, -f``: Follow log output
* ``--tail INTEGER``: Number of lines to show from the end

**Example:**

.. code-block:: bash

   qa-test run logs run_789012 --follow

Persona Management
------------------

qa-test personas
~~~~~~~~~~~~~~~~

Manage testing personas.

**Subcommands:**

list
^^^^

List available personas.

.. code-block:: bash

   qa-test personas list [OPTIONS]

**Options:**

* ``--industry TEXT``: Filter by industry

**Examples:**

.. code-block:: bash

   # List all personas
   qa-test personas list

   # List healthcare personas
   qa-test personas list --industry healthcare

industries
^^^^^^^^^^

List available industry templates.

.. code-block:: bash

   qa-test personas industries

**Example:**

.. code-block:: bash

   qa-test personas industries

create
^^^^^^

Create a custom persona.

.. code-block:: bash

   qa-test personas create [OPTIONS]

**Options:**

* ``--interactive, -i``: Use interactive wizard
* ``--file, -f PATH``: Save persona to file

**Examples:**

.. code-block:: bash

   # Interactive creation
   qa-test personas create --interactive

   # Save to file
   qa-test personas create --interactive --file ./my-personas.json

Model Management
----------------

qa-test models
~~~~~~~~~~~~~~

Manage LLM model configurations.

**Subcommands:**

list
^^^^

List recommended models by agent type and preset.

.. code-block:: bash

   qa-test models list [OPTIONS]

**Options:**

* ``--preset [development|balanced|enterprise]``: Show models for specific preset

**Examples:**

.. code-block:: bash

   # Show all presets
   qa-test models list

   # Show enterprise preset only
   qa-test models list --preset enterprise

recommend
^^^^^^^^^

Get model recommendations based on app characteristics.

.. code-block:: bash

   qa-test models recommend [OPTIONS] APP_SIZE

**Arguments:**

* ``APP_SIZE``: Application size [small|medium|large]

**Options:**

* ``--security-focused``: Prioritize security analysis accuracy
* ``--performance-focused``: Prioritize performance analysis

**Examples:**

.. code-block:: bash

   # Basic recommendation
   qa-test models recommend medium

   # Security-focused
   qa-test models recommend large --security-focused

test
^^^^

Test if a specific model configuration works.

.. code-block:: bash

   qa-test models test [OPTIONS] PROVIDER MODEL

**Arguments:**

* ``PROVIDER``: Model provider (ollama, openai, anthropic)
* ``MODEL``: Model name

**Options:**

* ``--prompt TEXT``: Test prompt (default: "Hello, please respond with a simple test message.")

**Examples:**

.. code-block:: bash

   # Test OpenAI model
   qa-test models test openai gpt-3.5-turbo

   # Test with custom prompt
   qa-test models test ollama llama3.2:latest --prompt "Analyze this API endpoint"

cost
^^^^

Estimate cost for running tests with different model presets.

.. code-block:: bash

   qa-test models cost [OPTIONS]

**Options:**

* ``--preset [development|balanced|enterprise]``: Model preset (default: balanced)
* ``--test-count INTEGER``: Estimated number of tests (default: 100)

**Examples:**

.. code-block:: bash

   # Estimate for balanced preset
   qa-test models cost --preset balanced --test-count 500

   # Compare presets
   qa-test models cost --preset development
   qa-test models cost --preset enterprise

Analytics
---------

qa-test analytics
~~~~~~~~~~~~~~~~~

View analytics and metrics.

**Subcommands:**

summary
^^^^^^^

Show analytics summary.

.. code-block:: bash

   qa-test analytics summary [OPTIONS]

**Options:**

* ``--days INTEGER``: Number of days to analyze (default: 30)

**Example:**

.. code-block:: bash

   qa-test analytics summary --days 7

project
^^^^^^^

Show analytics for a specific project.

.. code-block:: bash

   qa-test analytics project [OPTIONS] PROJECT_ID

**Arguments:**

* ``PROJECT_ID``: ID of the project

**Example:**

.. code-block:: bash

   qa-test analytics project proj_123456

Server Management
-----------------

qa-test server
~~~~~~~~~~~~~~

Start the web server for the QA testing interface.

.. code-block:: bash

   qa-test server [OPTIONS]

**Options:**

* ``--port INTEGER``: Port to run the server on (default: 8000)
* ``--host TEXT``: Host to bind the server to (default: localhost)

**Example:**

.. code-block:: bash

   qa-test server --port 8080 --host 0.0.0.0

System Management
-----------------

qa-test init
~~~~~~~~~~~~

Initialize the QA Agentic Testing system.

.. code-block:: bash

   qa-test init

This command:

* Sets up the database
* Creates default directories
* Shows available industry templates
* Provides next steps guidance

Environment Variables
---------------------

The CLI supports configuration through environment variables:

**Database Configuration:**

* ``QA_DATABASE_URL``: Database connection string (default: sqlite:///qa_testing.db)

**API Server Configuration:**

* ``QA_HOST``: Default host for server (default: 0.0.0.0)
* ``QA_PORT``: Default port for server (default: 8000)

**Testing Configuration:**

* ``QA_MAX_PERSONAS``: Maximum personas to load (default: 20)
* ``QA_MAX_SCENARIOS_PER_TYPE``: Maximum scenarios per type (default: 50)
* ``QA_EXECUTION_TIMEOUT``: Test execution timeout in seconds (default: 3600)

**Performance Configuration:**

* ``QA_ASYNC_ENABLED``: Enable async mode by default (default: true)
* ``QA_CONCURRENT_SCENARIOS``: Number of concurrent scenarios (default: 10)
* ``QA_MAX_CONCURRENT_FILES``: Maximum concurrent file operations (default: 20)

**Model Configuration:**

* ``QA_LLM_PROVIDER``: Default LLM provider (default: ollama)
* ``QA_LLM_MODEL``: Default LLM model (default: llama3.2:latest)
* ``QA_AGENT_TEMPERATURE``: Default temperature for agents (default: 0.7)

**Provider-Specific Configuration:**

* ``QA_SECURITY_PROVIDER``: Provider for security agents
* ``QA_SECURITY_MODEL``: Model for security agents
* ``QA_FUNCTIONAL_PROVIDER``: Provider for functional agents
* ``QA_FUNCTIONAL_MODEL``: Model for functional agents
* ``QA_PERFORMANCE_PROVIDER``: Provider for performance agents
* ``QA_PERFORMANCE_MODEL``: Model for performance agents

**API Keys:**

* ``OPENAI_API_KEY``: OpenAI API key
* ``ANTHROPIC_API_KEY``: Anthropic API key

Configuration Files
-------------------

**Global Configuration:**

Create ``~/.qa-testing/config.json`` for global settings:

.. code-block:: json

   {
     "default_model_preset": "balanced",
     "default_industry": "healthcare",
     "async_enabled": true,
     "max_concurrent_tests": 5
   }

**Project Configuration:**

Create ``qa_config.json`` in your project directory:

.. code-block:: json

   {
     "agents": {
       "security": {
         "provider": "openai",
         "model": "gpt-4",
         "temperature": 0.1
       },
       "functional": {
         "provider": "ollama",
         "model": "llama3.1:8b",
         "temperature": 0.2
       }
     },
     "personas": {
       "custom_personas_file": "./personas.json",
       "industry": "financial_services"
     }
   }

Exit Codes
----------

The CLI uses standard exit codes:

* ``0``: Success
* ``1``: General error
* ``2``: Misuse of shell command
* ``3``: Test failures detected
* ``4``: Configuration error
* ``5``: Network/API error

Examples
--------

Complete Testing Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Initialize system
   qa-test init

   # 2. Create project
   qa-test project create "MyApp" /path/to/app

   # 3. Run comprehensive testing
   qa-test /path/to/app \
     --industry healthcare \
     --model-preset balanced \
     --security-model openai/gpt-4 \
     --async \
     --format both

   # 4. View results
   qa-test run list --project-id proj_123456

   # 5. Get analytics
   qa-test analytics project proj_123456

CI/CD Integration
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Automated testing in CI/CD pipeline
   qa-test /path/to/app \
     --name "CI Validation" \
     --model-preset development \
     --output ./test-results \
     --format json

   # Check exit code for pass/fail
   if [ $? -eq 0 ]; then
     echo "QA tests passed"
   else
     echo "QA tests failed"
     exit 1
   fi

Cost-Optimized Testing
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Development testing (free)
   qa-test /path/to/app --model-preset development

   # Security validation (targeted)
   qa-test /path/to/app \
     --test-types security \
     --security-model openai/gpt-4

   # Performance analysis (specific endpoints)
   qa-test /path/to/critical-endpoints \
     --test-types performance \
     --performance-model anthropic/claude-3-opus
