Getting Started
===============

This guide will help you get started with QA Agentic Testing quickly and efficiently.

Installation
------------

Prerequisites
~~~~~~~~~~~~~

* Python 3.8 or higher
* pip package manager
* Optional: Ollama for local LLM models

Step 1: Install the Framework
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Navigate to QA testing framework
   cd apps/qa_agentic_testing

   # Install with async support
   pip install aiofiles asyncio
   pip install -e .

   # Initialize the system (one-time setup)
   qa-test init

Step 2: Test Your First App
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Example: User Management App**

.. code-block:: bash

   # Test the user_management app directly
   qa-test /path/to/apps/user_management

   # Results automatically saved to:
   # /path/to/apps/user_management/qa_results/
   #   ├── test_report.html      # Interactive dashboard
   #   ├── test_results.json     # Structured data
   #   └── execution_logs.txt    # Detailed logs

Step 3: View Results
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Open the HTML report in your browser
   open /path/to/apps/user_management/qa_results/test_report.html

   # Or start the web server for all results
   qa-test server --port 8000
   # Then visit: http://localhost:8000

Basic Usage Examples
--------------------

Simple One-Command Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Test any app with default settings
   qa-test /path/to/your/app

   # With async performance boost (3-5x faster)
   qa-test /path/to/your/app --async

Customized Testing
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Specify test types and interfaces
   qa-test /path/to/your/app \
     --name "Production Validation" \
     --interfaces cli web api \
     --test-types functional security performance usability \
     --format both \
     --output ./custom-reports

Project-Based Testing
~~~~~~~~~~~~~~~~~~~~~

For ongoing development:

.. code-block:: bash

   # Create a project for your app
   qa-test project create "MyApp" /path/to/your/app

   # List all projects
   qa-test project list

   # Run tests on the project
   qa-test project test <project-id> --async

   # View project analytics
   qa-test analytics project <project-id>

Understanding Results
---------------------

HTML Report Sections
~~~~~~~~~~~~~~~~~~~~~

* **Executive Summary**: Overall success rate, confidence score, key findings
* **Persona Results**: How different user types performed
* **Security Analysis**: Permission checks, vulnerabilities, compliance
* **Performance Metrics**: Response times, concurrent user handling
* **AI Insights**: Intelligent recommendations for improvement

JSON Data Structure
~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "metadata": {
       "app_path": "/path/to/your/app",
       "total_tests": 45,
       "success_rate": 87.3
     },
     "personas": {
       "system_admin": {"success_rate": 100.0, "tests": 12},
       "regular_user": {"success_rate": 85.2, "tests": 18}
     },
     "scenarios": {
       "functional": {"passed": 15, "failed": 2},
       "security": {"passed": 12, "failed": 1}
     }
   }

Next Steps
----------

Now that you have the basics working, explore:

* :doc:`personas` - Learn about the 27 built-in personas and industry templates
* :doc:`model_selection` - Optimize LLM model selection for your needs
* :doc:`agent_architecture` - Understand the advanced AI agent orchestration
* :doc:`examples/user_management` - Detailed walkthrough with a real application
