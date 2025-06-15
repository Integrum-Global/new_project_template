QA Agentic Testing Documentation
=================================

AI-powered autonomous testing with **async performance optimization** that discovers, analyzes, and tests any application with zero configuration. **3-5x faster** through concurrent operations and non-blocking I/O.

.. image:: https://img.shields.io/badge/Version-0.1.0-blue
   :alt: Version

.. image:: https://img.shields.io/badge/Performance-3x_faster-green
   :alt: Performance

.. image:: https://img.shields.io/badge/Personas-27_total-orange
   :alt: Personas

.. image:: https://img.shields.io/badge/Models-3_presets-purple
   :alt: Models

Overview
--------

The QA Agentic Testing framework provides comprehensive AI-powered testing with:

* **⚡ Async app discovery** - Concurrent file scanning and analysis (3x faster)
* **🧠 Intelligent persona generation** from discovered permissions and roles
* **🔄 Concurrent scenario creation** - Parallel test generation (4.5x faster)
* **🤖 AI agent consensus testing** with A2A communication and self-organizing pools
* **📊 Non-blocking report generation** - Simultaneous HTML/JSON creation

Quick Start
-----------

.. code-block:: bash

   # Install and initialize
   cd apps/qa_agentic_testing
   pip install -e .
   qa-test init

   # Test your application
   qa-test /path/to/your/app --async

   # Results automatically saved to:
   # /path/to/your/app/qa_results/test_report.html

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   getting_started
   user_workflow
   personas
   model_selection
   agent_architecture
   cli_reference

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/personas
   api/agents
   api/cli

.. toctree::
   :maxdepth: 2
   :caption: Examples & Tutorials

   examples/user_management
   examples/healthcare_app
   examples/financial_services
   examples/manufacturing

.. toctree::
   :maxdepth: 1
   :caption: Advanced Topics

   advanced/orchestration_patterns
   advanced/performance_optimization
   advanced/custom_personas
   advanced/enterprise_deployment

.. toctree::
   :maxdepth: 1
   :caption: Reference

   changelog
   troubleshooting
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
