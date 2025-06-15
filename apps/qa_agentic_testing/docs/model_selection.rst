LLM Model Selection Guide
=========================

The QA Agentic Testing framework supports multiple LLM providers and models, each optimized for different testing scenarios. This guide helps you choose the right models for your specific needs.

Supported Providers
-------------------

Ollama (Local Models)
~~~~~~~~~~~~~~~~~~~~~~

* **Cost**: Free (local computation)
* **Latency**: Low (no network calls)
* **Privacy**: High (data stays local)
* **Models**: ``llama3.2:latest``, ``llama3.1:8b``, ``codellama:13b``
* **Best for**: Development, testing, cost-sensitive deployments

OpenAI
~~~~~~

* **Cost**: Pay-per-token (moderate to high)
* **Latency**: Medium (API calls)
* **Quality**: High (especially GPT-4)
* **Models**: ``gpt-3.5-turbo``, ``gpt-4``, ``gpt-4-turbo``
* **Best for**: Production security analysis, complex reasoning

Anthropic Claude
~~~~~~~~~~~~~~~~

* **Cost**: Pay-per-token (moderate to high)
* **Latency**: Medium (API calls)
* **Quality**: High (excellent for analysis)
* **Models**: ``claude-3-haiku``, ``claude-3-sonnet``, ``claude-3-opus``
* **Best for**: Performance analysis, UX evaluation, detailed reports

Model Selection by Agent Type
------------------------------

Security Analysis Agents
~~~~~~~~~~~~~~~~~~~~~~~~~

**Recommended Models:**

* **Production**: ``openai/gpt-4`` or ``anthropic/claude-3-sonnet``
* **Development**: ``ollama/llama3.2:latest``

**Rationale**: Security analysis requires high accuracy and comprehensive threat detection. Premium models excel at identifying subtle security issues and compliance violations.

**Configuration:**

.. code-block:: bash

   qa-test /path/to/app --security-model openai/gpt-4

Functional Testing Agents
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Recommended Models:**

* **Production**: ``openai/gpt-3.5-turbo`` or ``anthropic/claude-3-haiku``
* **Development**: ``ollama/llama3.1:8b``

**Rationale**: Functional testing benefits from balanced performance and cost. Mid-tier models provide good coverage without excessive costs.

**Configuration:**

.. code-block:: bash

   qa-test /path/to/app --functional-model anthropic/claude-3-haiku

Performance Analysis Agents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Recommended Models:**

* **Production**: ``anthropic/claude-3-opus`` or ``openai/gpt-4``
* **Development**: ``ollama/codellama:13b``

**Rationale**: Performance analysis requires analytical depth and understanding of complex metrics. Top-tier models provide better insights into optimization opportunities.

**Configuration:**

.. code-block:: bash

   qa-test /path/to/app --performance-model anthropic/claude-3-opus

Usability Assessment Agents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Recommended Models:**

* **Production**: ``anthropic/claude-3-sonnet``
* **Development**: ``ollama/llama3.2:latest``

**Rationale**: Usability evaluation benefits from models with strong reasoning about human behavior and user experience patterns.

Integration Testing Agents
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Recommended Models:**

* **Production**: ``openai/gpt-4``
* **Development**: ``ollama/codellama:latest``

**Rationale**: API and integration testing requires technical precision and understanding of complex system interactions.

Preset Configurations
----------------------

Development Preset
~~~~~~~~~~~~~~~~~~~

**Target**: Local development and testing
**Cost**: Free (Ollama only)
**Performance**: Good for basic testing

.. code-block:: text

   Basic LLM:           ollama/llama3.2:latest
   Iterative Agent:     ollama/llama3.1:8b
   A2A Agent:           ollama/llama3.2:latest
   Self-Organizing:     ollama/codellama:13b
   MCP Agent:           ollama/llama3.1:8b

**Usage:**

.. code-block:: bash

   qa-test /path/to/app --model-preset development

Balanced Preset
~~~~~~~~~~~~~~~

**Target**: Production use with cost optimization
**Cost**: Medium (mix of local and API models)
**Performance**: Excellent balance of quality and cost

.. code-block:: text

   Basic LLM:           openai/gpt-3.5-turbo
   Iterative Agent:     ollama/llama3.1:8b
   A2A Agent:           openai/gpt-3.5-turbo
   Self-Organizing:     anthropic/claude-3-haiku
   MCP Agent:           ollama/codellama:latest

**Usage:**

.. code-block:: bash

   qa-test /path/to/app --model-preset balanced

Enterprise Preset
~~~~~~~~~~~~~~~~~~

**Target**: Mission-critical applications
**Cost**: High (premium API models)
**Performance**: Maximum quality and comprehensive analysis

.. code-block:: text

   Basic LLM:           openai/gpt-4
   Iterative Agent:     anthropic/claude-3-sonnet
   A2A Agent:           openai/gpt-4
   Self-Organizing:     anthropic/claude-3-opus
   MCP Agent:           openai/gpt-4

**Usage:**

.. code-block:: bash

   qa-test /path/to/app --model-preset enterprise

Application Size Recommendations
---------------------------------

Small Applications (< 10 endpoints)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Preset**: ``development``
* **Rationale**: Simple applications don't require premium models
* **Estimated Cost**: $0 (local models only)

Medium Applications (10-50 endpoints)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Preset**: ``balanced``
* **Custom Security**: Consider ``--security-model openai/gpt-4`` for sensitive apps
* **Estimated Cost**: $5-20 per 100 test runs

Large Applications (50+ endpoints)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Preset**: ``enterprise``
* **Specialized Models**: Use specific models per analysis type
* **Estimated Cost**: $50-200 per 100 test runs

Enterprise Applications (100+ endpoints)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Preset**: ``enterprise``
* **Security Focus**: ``--security-model openai/gpt-4``
* **Performance Focus**: ``--performance-model anthropic/claude-3-opus``
* **Estimated Cost**: $100-500 per 100 test runs

Cost Optimization Strategies
-----------------------------

Tiered Testing Approach
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Initial testing with development models
   qa-test /path/to/app --model-preset development

   # Security validation with premium models
   qa-test /path/to/app --security-model openai/gpt-4 --test-types security

   # Performance analysis for critical paths only
   qa-test /path/to/critical-endpoints --performance-model anthropic/claude-3-opus

Environment-Based Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Development environment
   export QA_MODEL_PRESET=development

   # Staging environment
   export QA_MODEL_PRESET=balanced
   export QA_SECURITY_MODEL=openai/gpt-4

   # Production validation
   export QA_MODEL_PRESET=enterprise

Selective Testing
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Test only critical functionality with premium models
   qa-test /path/to/app --test-types security --security-model openai/gpt-4

   # Use local models for routine functional testing
   qa-test /path/to/app --test-types functional --model-preset development

Performance vs. Cost Matrix
----------------------------

.. list-table::
   :header-rows: 1

   * - Preset
     - Quality
     - Speed
     - Cost/100 Tests
     - Best For
   * - Development
     - Good
     - Fast
     - $0
     - Local dev, CI/CD
   * - Balanced
     - Excellent
     - Medium
     - $10-30
     - Staging, pre-prod
   * - Enterprise
     - Superior
     - Medium
     - $100-300
     - Production, compliance

Environment Setup
-----------------

Ollama Setup
~~~~~~~~~~~~

.. code-block:: bash

   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh

   # Pull required models
   ollama pull llama3.2:latest
   ollama pull llama3.1:8b
   ollama pull codellama:13b

   # Start Ollama service
   ollama serve

API Provider Setup
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # OpenAI
   export OPENAI_API_KEY=your-openai-api-key

   # Anthropic
   export ANTHROPIC_API_KEY=your-anthropic-api-key

   # Test connectivity
   qa-test models test openai gpt-3.5-turbo
   qa-test models test anthropic claude-3-haiku

CLI Commands Reference
----------------------

List Available Models
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Show all presets
   qa-test models list

   # Show specific preset
   qa-test models list --preset enterprise

Get Recommendations
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Based on app size
   qa-test models recommend medium

   # Security-focused recommendations
   qa-test models recommend large --security-focused

   # Performance-focused recommendations
   qa-test models recommend medium --performance-focused

Test Model Connectivity
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Test specific model
   qa-test models test openai gpt-4

   # Test with custom prompt
   qa-test models test ollama llama3.2:latest --prompt "Analyze this API endpoint"

Cost Estimation
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Estimate costs for preset
   qa-test models cost --preset enterprise --test-count 500

   # Compare presets
   qa-test models cost --preset development
   qa-test models cost --preset balanced
   qa-test models cost --preset enterprise

Best Practices
--------------

Start Small, Scale Up
~~~~~~~~~~~~~~~~~~~~~

1. Begin with ``development`` preset for initial testing
2. Use ``balanced`` for comprehensive validation
3. Apply ``enterprise`` only for critical production testing

Specialized Models for Critical Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Always use premium models for security analysis in production
2. Use analytical models (Claude Opus, GPT-4) for performance insights
3. Consider local models sufficient for basic functional testing

Budget Management
~~~~~~~~~~~~~~~~~

1. Set up cost monitoring for API usage
2. Use tiered testing strategies
3. Consider monthly budgets per environment

Quality Assurance
~~~~~~~~~~~~~~~~~

1. Validate model outputs with known test cases
2. Compare results across different models for critical analysis
3. Monitor model performance over time

Security Considerations
~~~~~~~~~~~~~~~~~~~~~~~

1. Keep API keys secure and rotated
2. Use local models for sensitive data when possible
3. Monitor API usage for unusual patterns

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Ollama Connection Errors:**

.. code-block:: bash

   # Check if Ollama is running
   curl http://localhost:11434/api/tags

   # Start Ollama service
   ollama serve

   # Pull missing models
   ollama pull llama3.2:latest

**API Key Issues:**

.. code-block:: bash

   # Verify API key format
   echo $OPENAI_API_KEY | wc -c  # Should be ~51 characters for OpenAI

   # Test API connectivity
   qa-test models test openai gpt-3.5-turbo --prompt "test"

**Model Not Found:**

.. code-block:: bash

   # List available models
   ollama list                    # For Ollama
   qa-test models list           # For all presets

**High Costs:**

.. code-block:: bash

   # Switch to development preset
   qa-test /path/to/app --model-preset development

   # Use selective testing
   qa-test /path/to/app --test-types functional --model-preset development
   qa-test /path/to/app --test-types security --security-model openai/gpt-4
