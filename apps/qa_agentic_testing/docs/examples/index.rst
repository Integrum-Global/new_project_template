Examples and Use Cases
======================

This section provides practical examples of using the QA Agentic Testing framework across different application types and testing scenarios.

Quick Examples
--------------

Basic Application Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Simple functional testing
   qa-test /path/to/your/app

   # With industry-specific personas
   qa-test /path/to/your/app --industry healthcare

   # Security-focused testing
   qa-test /path/to/your/app --test-types security --security-model openai/gpt-4

Comprehensive Testing Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Complete testing pipeline
   qa-test /path/to/your/app \
     --name "Production Validation" \
     --industry financial_services \
     --interfaces cli web api \
     --test-types functional security performance \
     --model-preset enterprise \
     --async \
     --format both

Application-Specific Examples
-----------------------------

.. toctree::
   :maxdepth: 2

   user_management

Industry-Specific Testing
-------------------------

Financial Services Applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Focus Areas:**
   - SOX compliance validation
   - Trading system performance
   - Risk management workflows
   - Audit trail verification

**Example Command:**

.. code-block:: bash

   qa-test /path/to/trading-app \
     --industry financial_services \
     --test-types security performance \
     --security-model openai/gpt-4 \
     --performance-model anthropic/claude-3-opus

**Key Personas:**
   - Compliance Officer: Regulatory validation
   - Trading Desk User: High-frequency operations
   - Risk Analyst: Risk model validation
   - Portfolio Manager: Investment strategy testing

Healthcare Applications
~~~~~~~~~~~~~~~~~~~~~~~

**Focus Areas:**
   - HIPAA compliance
   - Patient data protection
   - Clinical workflow validation
   - Medical device integration

**Example Command:**

.. code-block:: bash

   qa-test /path/to/ehr-system \
     --industry healthcare \
     --test-types security functional \
     --security-model openai/gpt-4

**Key Personas:**
   - Clinical User: Patient care workflows
   - Privacy Officer: HIPAA compliance
   - Hospital Administrator: System management
   - Lab Technician: Laboratory processes

Manufacturing Applications
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Focus Areas:**
   - Production line monitoring
   - Quality control processes
   - Safety compliance
   - Equipment maintenance

**Example Command:**

.. code-block:: bash

   qa-test /path/to/mes-system \
     --industry manufacturing \
     --test-types functional performance \
     --async

**Key Personas:**
   - Plant Manager: Production oversight
   - Quality Inspector: Quality assurance
   - Maintenance Technician: Equipment care
   - Safety Coordinator: Compliance monitoring

E-commerce Applications
~~~~~~~~~~~~~~~~~~~~~~~

**Focus Areas:**
   - Customer experience optimization
   - Payment security
   - Inventory management
   - Fraud detection

**Example Command:**

.. code-block:: bash

   qa-test /path/to/ecommerce-platform \
     --industry retail_ecommerce \
     --test-types functional security performance \
     --model-preset balanced

**Key Personas:**
   - Customer Service Rep: Support workflows
   - Inventory Manager: Stock management
   - Marketing Analyst: Campaign optimization
   - Fraud Analyst: Security validation

Testing Patterns by Application Size
------------------------------------

Small Applications (< 10 endpoints)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Recommended Approach:**

.. code-block:: bash

   # Cost-effective testing with local models
   qa-test /path/to/small-app --model-preset development

**Characteristics:**
   - 2-3 personas sufficient
   - 5-15 test scenarios
   - Basic functional and security testing
   - Execution time: 1-3 minutes

Medium Applications (10-50 endpoints)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Recommended Approach:**

.. code-block:: bash

   # Balanced testing with mixed models
   qa-test /path/to/medium-app \
     --model-preset balanced \
     --security-model openai/gpt-4

**Characteristics:**
   - 5-8 personas recommended
   - 20-50 test scenarios
   - Comprehensive testing across all types
   - Execution time: 5-15 minutes

Large Applications (50+ endpoints)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Recommended Approach:**

.. code-block:: bash

   # Enterprise testing with premium models
   qa-test /path/to/large-app \
     --model-preset enterprise \
     --async \
     --concurrent-scenarios 10

**Characteristics:**
   - 8-12 personas for comprehensive coverage
   - 50-150 test scenarios
   - Full testing suite with performance analysis
   - Execution time: 15-45 minutes (async: 5-15 minutes)

Advanced Testing Scenarios
--------------------------

API-First Applications
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Focus on API functionality and performance
   qa-test /path/to/api-app \
     --interfaces api \
     --test-types functional performance security \
     --performance-model anthropic/claude-3-opus

**Testing Focus:**
   - Endpoint functionality validation
   - Rate limiting and performance
   - Authentication and authorization
   - Data validation and error handling

CLI Applications
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Command-line interface testing
   qa-test /path/to/cli-app \
     --interfaces cli \
     --test-types functional usability \
     --discover-personas

**Testing Focus:**
   - Command syntax validation
   - Help system effectiveness
   - Error message clarity
   - User workflow optimization

Web Applications
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Full-stack web application testing
   qa-test /path/to/web-app \
     --interfaces web \
     --test-types functional usability security \
     --model-preset balanced

**Testing Focus:**
   - User interface validation
   - Form functionality
   - Navigation and workflows
   - Accessibility compliance

Multi-Interface Applications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Comprehensive multi-interface testing
   qa-test /path/to/full-app \
     --interfaces cli web api mobile \
     --test-types functional security performance usability \
     --model-preset enterprise \
     --async

**Testing Focus:**
   - Cross-platform consistency
   - Interface-specific optimizations
   - Integration between interfaces
   - User experience coherence

Custom Configuration Examples
----------------------------

Environment-Specific Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Development Environment:**

.. code-block:: bash

   export QA_MODEL_PRESET=development
   export QA_ASYNC_ENABLED=true
   qa-test /path/to/app

**Staging Environment:**

.. code-block:: bash

   export QA_MODEL_PRESET=balanced
   export QA_SECURITY_MODEL=openai/gpt-4
   qa-test /path/to/app --test-types security

**Production Validation:**

.. code-block:: bash

   export QA_MODEL_PRESET=enterprise
   qa-test /path/to/app --format json --output ./compliance-reports

Cost-Optimized Testing
~~~~~~~~~~~~~~~~~~~~~~

**Tiered Testing Strategy:**

.. code-block:: bash

   # Phase 1: Basic validation (free)
   qa-test /path/to/app --model-preset development

   # Phase 2: Security analysis (targeted cost)
   qa-test /path/to/app --test-types security --security-model openai/gpt-4

   # Phase 3: Performance optimization (premium analysis)
   qa-test /path/to/critical-paths --test-types performance --performance-model anthropic/claude-3-opus

Integration Examples
--------------------

CI/CD Pipeline Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~

**GitHub Actions:**

.. code-block:: yaml

   name: QA Agentic Testing
   on: [push, pull_request]

   jobs:
     qa-testing:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Run QA Tests
           run: |
             pip install -e apps/qa_agentic_testing
             qa-test ${{ github.workspace }} \
               --model-preset development \
               --format json \
               --output ./qa-results
         - name: Upload Results
           uses: actions/upload-artifact@v3
           with:
             name: qa-results
             path: ./qa-results

**Jenkins Pipeline:**

.. code-block:: groovy

   pipeline {
       agent any
       stages {
           stage('QA Testing') {
               steps {
                   sh '''
                       cd apps/qa_agentic_testing
                       pip install -e .
                       qa-test ${WORKSPACE} --format json --output ./qa-results
                   '''
               }
               post {
                   always {
                       archiveArtifacts artifacts: 'qa-results/**/*', allowEmptyArchive: true
                   }
               }
           }
       }
   }

API Integration
~~~~~~~~~~~~~~~

**Python Integration:**

.. code-block:: python

   import asyncio
   from qa_agentic_testing import AutonomousQATester
   from pathlib import Path

   async def run_qa_test():
       app_path = Path("/path/to/app")
       tester = AutonomousQATester(app_path=app_path)

       # Discover application structure
       analysis = tester.discover_app(app_path)

       # Generate personas and scenarios
       personas = tester.generate_personas()
       scenarios = tester.generate_scenarios(personas[:5])

       # Execute tests
       results = await tester.execute_tests()

       # Generate report
       report_path = tester.generate_report("comprehensive_report.html")
       return report_path

   # Run the test
   report = asyncio.run(run_qa_test())
   print(f"QA report generated: {report}")

**REST API Usage:**

.. code-block:: python

   import requests

   # Start QA testing server
   # qa-test server --port 8000

   base_url = "http://localhost:8000/api"

   # Create project
   project_data = {
       "name": "My Application",
       "app_path": "/path/to/app",
       "description": "Comprehensive testing"
   }

   response = requests.post(f"{base_url}/projects", json=project_data)
   project = response.json()

   # Create and start test run
   run_data = {
       "project_id": project["project_id"],
       "name": "Production Validation"
   }

   response = requests.post(f"{base_url}/runs", json=run_data)
   run = response.json()

   # Start execution
   requests.post(f"{base_url}/runs/{run['run_id']}/start")

   # Monitor progress
   status = requests.get(f"{base_url}/runs/{run['run_id']}/status")
   print(f"Test status: {status.json()}")

Monitoring and Analytics
-----------------------

Real-time Monitoring
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Start monitoring server
   qa-test server --port 8080

   # Access monitoring dashboards:
   # http://localhost:8080/projects - Project overview
   # http://localhost:8080/runs/real-time - Live test execution
   # http://localhost:8080/analytics - Performance metrics

Performance Analytics
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Get analytics summary
   qa-test analytics summary --days 30

   # Project-specific analytics
   qa-test analytics project proj_12345

   # Export analytics data
   qa-test analytics export --format csv --output ./analytics.csv

Troubleshooting Examples
------------------------

Common Issues and Solutions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Model Connection Issues:**

.. code-block:: bash

   # Test model connectivity
   qa-test models test ollama llama3.2:latest
   qa-test models test openai gpt-3.5-turbo

   # Check Ollama service
   curl http://localhost:11434/api/tags

**Permission Errors:**

.. code-block:: bash

   # Verify app access
   ls -la /path/to/app

   # Check database permissions
   qa-test init  # Reinitialize if needed

**High API Costs:**

.. code-block:: bash

   # Switch to development models
   qa-test /path/to/app --model-preset development

   # Estimate costs before running
   qa-test models cost --preset enterprise --test-count 100

Best Practices
--------------

1. **Start Simple**: Begin with development preset for initial validation
2. **Industry-Specific**: Use appropriate industry personas for domain expertise
3. **Incremental Testing**: Build up from functional to comprehensive testing
4. **Cost Management**: Use tiered testing approach for budget control
5. **Automation**: Integrate into CI/CD for continuous validation
6. **Monitoring**: Use analytics to track testing effectiveness over time

For more detailed examples, see the specific application guides in the examples directory.
