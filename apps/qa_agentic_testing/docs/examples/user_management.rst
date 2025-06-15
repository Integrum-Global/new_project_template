User Management App Testing Example
====================================

This example demonstrates comprehensive testing of the User Management application using the QA Agentic Testing framework with persona-based testing and LLM model configuration.

Application Overview
--------------------

The User Management app (``apps/user_management``) provides:

* **User Registration & Authentication**: Account creation, login, password management
* **Role-Based Access Control**: Admin, Manager, User roles with different permissions
* **Django Admin Interface**: Web-based administration panel
* **API Endpoints**: RESTful API for user operations
* **Database Integration**: PostgreSQL with user data and audit logs

Quick Start Testing
--------------------

Basic Testing
~~~~~~~~~~~~~

.. code-block:: bash

   # Basic functional testing
   qa-test /path/to/apps/user_management

   # This performs:
   # ✓ App discovery and analysis
   # ✓ Persona-based testing with built-in personas
   # ✓ Functional, security, and usability testing
   # ✓ HTML report generation

Healthcare Organization Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Healthcare-specific persona testing
   qa-test /path/to/apps/user_management \
     --industry healthcare \
     --name "Hospital User Management Validation" \
     --interfaces web api \
     --test-types functional security \
     --async

   # This loads:
   # ✓ Healthcare personas (Clinical User, Privacy Officer, etc.)
   # ✓ HIPAA compliance testing scenarios
   # ✓ Medical role permission validation
   # ✓ Privacy-focused security analysis

Enterprise Security Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Security-focused testing with premium models
   qa-test /path/to/apps/user_management \
     --model-preset enterprise \
     --security-model openai/gpt-4 \
     --test-types security \
     --format both

   # This provides:
   # ✓ Advanced security analysis with GPT-4
   # ✓ Compliance validation
   # ✓ Role escalation testing
   # ✓ Detailed security reports

Detailed Testing Scenarios
---------------------------

Persona-Based Testing Matrix
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The User Management app testing covers these persona scenarios:

**Administrative Scenarios:**

* **System Admin (Alice)**: Full system access validation
  - User creation, modification, deletion
  - Role assignment and permission management
  - System configuration and security settings
  - Audit log access and compliance reporting

* **Security Officer (Sarah)**: Security and compliance focus
  - Password policy enforcement
  - Access control validation
  - Security event monitoring
  - Compliance audit trail verification

**Business User Scenarios:**

* **Manager (Mark)**: Department-level operations
  - Team member management
  - Department-specific user access
  - Limited administrative capabilities
  - Reporting and analytics access

* **Regular User (Rachel)**: Standard user workflows
  - Profile management and self-service
  - Password changes and account updates
  - Basic functionality validation
  - User experience optimization

* **New User (Nancy)**: Onboarding experience
  - Registration process validation
  - First-time user experience
  - Help system and documentation
  - Learning curve assessment

Industry-Specific Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Healthcare Organization:**

.. code-block:: bash

   qa-test /path/to/apps/user_management --industry healthcare

**Testing Focus:**
   - HIPAA compliance validation
   - Medical staff role permissions
   - Patient data access controls
   - Audit logging for healthcare regulations

**Key Personas:**
   - Clinical User (Dr. Clara): Patient record access
   - Privacy Officer (Patricia): HIPAA compliance
   - Hospital Administrator (Harold): Staff management
   - Nurse Practitioner (Nancy): Care coordination access

**Financial Services Organization:**

.. code-block:: bash

   qa-test /path/to/apps/user_management --industry financial_services

**Testing Focus:**
   - SOX compliance requirements
   - Trading desk user permissions
   - Risk management access controls
   - Financial audit trail validation

**Key Personas:**
   - Compliance Officer (Catherine): Regulatory validation
   - Trading Desk User (Thomas): High-frequency access
   - Risk Analyst (Rebecca): Risk assessment tools
   - Portfolio Manager (Patrick): Client data access

Agent Architecture in Action
-----------------------------

Basic LLM Agents
~~~~~~~~~~~~~~~~

**Usage**: Initial app discovery and basic validation

.. code-block:: python

   # User registration validation
   basic_agent.analyze_scenario(
       scenario="New user registration process",
       persona="Nancy Newbie",
       focus_areas=["usability", "functionality"]
   )

**Analysis Output:**
   - Form validation effectiveness
   - Error message clarity
   - Registration flow completeness
   - Success/failure rate prediction

Iterative LLM Agents
~~~~~~~~~~~~~~~~~~~~~

**Usage**: Complex permission optimization analysis

.. code-block:: python

   # Multi-iteration role permission optimization
   iterative_agent.optimize_permissions(
       scenario="Role-based access control review",
       persona="Mark Manager",
       iterations=5
   )

**Iteration Flow:**
   1. **Iteration 1**: Identify permission inconsistencies
   2. **Iteration 2**: Analyze role hierarchy conflicts
   3. **Iteration 3**: Generate permission optimization recommendations
   4. **Iteration 4**: Validate against security requirements
   5. **Iteration 5**: Finalize role-permission matrix

A2A Agent Communication
~~~~~~~~~~~~~~~~~~~~~~~

**Usage**: Security vs. usability balance validation

.. code-block:: python

   # Cross-validation between security and usability agents
   security_agent.analyze("Password policy enforcement")
   usability_agent.analyze("User experience with password requirements")
   coordinator.build_consensus()

**Communication Example:**

.. code-block:: text

   Security Agent: "Password policy requires 12+ chars, symbols, frequent rotation"
   Usability Agent: "Complex requirements cause user frustration and workarounds"
   Security Agent: "Suggest balanced policy: 10+ chars, optional MFA for sensitive data"
   Usability Agent: "Agreed - user education + graduated security based on data sensitivity"
   Coordinator: "Consensus: Implement tiered password policy with user-friendly MFA options"

Self-Organizing Agent Pools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Usage**: Enterprise-scale user management testing

.. code-block:: python

   # Dynamic team formation for comprehensive testing
   pool_manager.form_team_for_scenario(
       scenario="Enterprise user lifecycle management",
       complexity="high",
       focus_areas=["security", "compliance", "performance", "usability"]
   )

**Team Formation:**
   - **Security Specialist**: Permission validation, audit compliance
   - **Performance Analyst**: Database query optimization, response times
   - **Usability Expert**: User experience flows, accessibility
   - **Integration Specialist**: API endpoint validation, external systems

Model Configuration Examples
-----------------------------

Development Environment
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Cost-free local testing
   qa-test /path/to/apps/user_management --model-preset development

   # Uses Ollama models:
   # ✓ Basic analysis: llama3.2:latest
   # ✓ Security scan: llama3.2:latest
   # ✓ Performance check: codellama:13b

**Best For:**
   - Local development validation
   - CI/CD pipeline integration
   - Rapid iteration testing

Staging Environment
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Balanced cost and quality
   qa-test /path/to/apps/user_management \
     --model-preset balanced \
     --security-model openai/gpt-4

   # Uses mixed models:
   # ✓ Functional testing: gpt-3.5-turbo
   # ✓ Security analysis: gpt-4 (premium)
   # ✓ Performance analysis: claude-3-haiku

**Best For:**
   - Pre-production validation
   - Comprehensive testing with cost control
   - Security-critical analysis

Production Validation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Maximum quality analysis
   qa-test /path/to/apps/user_management \
     --model-preset enterprise \
     --security-model openai/gpt-4 \
     --performance-model anthropic/claude-3-opus

   # Uses premium models:
   # ✓ All analysis: GPT-4, Claude-3-Opus
   # ✓ Maximum accuracy and depth
   # ✓ Comprehensive compliance validation

**Best For:**
   - Production deployment validation
   - Compliance auditing
   - Mission-critical security analysis

Expected Test Results
---------------------

Test Coverage Matrix
~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Test Category
     - Scenarios Tested
     - Success Criteria
     - Typical Results
   * - User Registration
     - 15 scenarios
     - >90% success rate
     - 92-98% pass rate
   * - Authentication
     - 12 scenarios
     - >95% security compliance
     - 94-99% pass rate
   * - Role Management
     - 20 scenarios
     - >85% permission accuracy
     - 88-94% pass rate
   * - API Endpoints
     - 25 scenarios
     - >90% functionality
     - 91-97% pass rate
   * - Security Analysis
     - 18 scenarios
     - >98% vulnerability detection
     - 96-100% detection rate

Sample Test Report Output
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   🎯 User Management Testing Results
   ═══════════════════════════════════════

   📊 Overall Success Rate: 94.2%
   ⏱️  Total Execution Time: 3.2 minutes
   🤖 Personas Tested: 7 (Healthcare industry)
   📋 Scenarios Executed: 89

   ✅ Functional Testing: 96.1% (43/45 passed)
   🔒 Security Analysis: 92.3% (24/26 passed)
   ⚡ Performance Check: 94.7% (18/19 passed)
   👥 Usability Review: 93.8% (15/16 passed)

   🚨 Critical Issues Found:
   • Password reset vulnerability (Security)
   • Slow user search queries (Performance)

   💡 Recommendations:
   • Implement rate limiting for password reset
   • Add database indexing for user search
   • Consider MFA for admin accounts

Configuration Files
--------------------

Project-Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create ``qa_config.json`` in your User Management app directory:

.. code-block:: json

   {
     "agents": {
       "security": {
         "provider": "openai",
         "model": "gpt-4",
         "temperature": 0.1,
         "focus_areas": ["authentication", "authorization", "data_protection"]
       },
       "functional": {
         "provider": "ollama",
         "model": "llama3.1:8b",
         "temperature": 0.2,
         "focus_areas": ["user_workflows", "api_functionality", "database_operations"]
       }
     },
     "personas": {
       "industry": "healthcare",
       "custom_personas": [
         {
           "key": "hipaa_auditor",
           "name": "HIPAA Compliance Auditor",
           "permissions": ["audit:*", "compliance:*", "privacy:*"],
           "expected_success_rate": 98.0
         }
       ]
     },
     "testing": {
       "max_concurrent_scenarios": 5,
       "timeout_minutes": 15,
       "retry_failed_tests": true
     }
   }

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # User Management specific configuration
   export QA_DATABASE_URL="postgresql://user:pass@localhost/user_mgmt_test"
   export QA_USER_MGMT_ADMIN_URL="http://localhost:8000/admin/"
   export QA_USER_MGMT_API_BASE="http://localhost:8000/api/v1/"

   # Model configuration
   export QA_LLM_PROVIDER="openai"
   export QA_SECURITY_MODEL="gpt-4"
   export OPENAI_API_KEY="your-openai-key"

Automation and CI/CD
---------------------

GitHub Actions Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: QA Agentic Testing
   on: [push, pull_request]

   jobs:
     qa-testing:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Setup QA Testing
           run: |
             cd apps/qa_agentic_testing
             pip install -e .
             qa-test init

         - name: Run User Management Tests
           run: |
             qa-test apps/user_management \
               --model-preset development \
               --format json \
               --output ./qa-results

         - name: Upload Results
           uses: actions/upload-artifact@v3
           with:
             name: qa-test-results
             path: ./qa-results/

Pre-commit Hook
~~~~~~~~~~~~~~~

.. code-block:: bash

   #!/bin/bash
   # .git/hooks/pre-commit

   echo "Running QA Agentic Testing..."
   qa-test apps/user_management --model-preset development --format json

   if [ $? -ne 0 ]; then
     echo "QA tests failed. Commit aborted."
     exit 1
   fi

   echo "QA tests passed. Proceeding with commit."

Advanced Features
-----------------

Custom Scenario Generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Generate scenarios specific to User Management app
   from core.scenario_generator import ScenarioGenerator
   from core.personas import PersonaManager

   generator = ScenarioGenerator()
   persona_manager = PersonaManager()

   # Load healthcare personas
   personas = persona_manager.load_industry_personas("healthcare")

   # Generate custom scenarios
   scenarios = generator.generate_scenarios(
       app_path="/path/to/apps/user_management",
       personas=personas,
       focus_areas=["user_lifecycle", "permission_management", "audit_compliance"]
   )

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Async testing for faster execution
   qa-test /path/to/apps/user_management \
     --async \
     --concurrent-scenarios 10 \
     --max-concurrent-files 20

   # Results in 3-5x faster execution:
   # Standard: ~15 minutes for comprehensive testing
   # Async: ~3-5 minutes for same coverage

Real-time Monitoring
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start web server for real-time monitoring
   qa-test server --port 8080

   # View testing progress at:
   # http://localhost:8080/projects
   # http://localhost:8080/runs/real-time

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Database Connection Errors:**

.. code-block:: bash

   # Verify database is running
   psql -h localhost -U postgres -d user_management_test

   # Check configuration
   qa-test init  # Recreates default config

**Model Authentication Errors:**

.. code-block:: bash

   # Test model connectivity
   qa-test models test openai gpt-3.5-turbo
   qa-test models test ollama llama3.2:latest

**Permission Denied Errors:**

.. code-block:: bash

   # Check app permissions
   ls -la /path/to/apps/user_management

   # Verify user has read access to app directory

Next Steps
----------

1. **Explore Advanced Scenarios**: Create custom personas for your specific user roles
2. **Integration Testing**: Test User Management with other apps in your ecosystem
3. **Performance Benchmarking**: Establish baseline performance metrics
4. **Compliance Validation**: Regular testing for industry-specific requirements
5. **Continuous Monitoring**: Set up automated testing in your CI/CD pipeline

For more examples and advanced configurations, see the `User Management Workflows <../../user_management/workflows/>`_ directory.
