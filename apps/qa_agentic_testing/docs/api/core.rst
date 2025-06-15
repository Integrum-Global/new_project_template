Core API Reference
==================

This section documents the core classes and functions of the QA Agentic Testing framework.

Test Executor
-------------

.. automodule:: core.test_executor
   :members:
   :undoc-members:
   :show-inheritance:

AutonomousQATester
~~~~~~~~~~~~~~~~~~

.. autoclass:: core.test_executor.AutonomousQATester
   :members:
   :undoc-members:
   :show-inheritance:

   The main class for autonomous QA testing of applications. This class orchestrates
   the entire testing process from app discovery to report generation.

   **Example Usage:**

   .. code-block:: python

      from core.test_executor import AutonomousQATester

      # Initialize tester
      tester = AutonomousQATester(
          app_path=Path("/path/to/app"),
          output_dir=Path("./qa_results")
      )

      # Run complete testing pipeline
      summary = await tester.quick_test(app_path)
      print(f"Success rate: {summary.success_rate}%")

TestResult
~~~~~~~~~~

.. autoclass:: core.test_executor.TestResult
   :members:
   :undoc-members:
   :show-inheritance:

   Represents the result of a single test execution with detailed metrics and analysis.

TestExecutionSummary
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: core.test_executor.TestExecutionSummary
   :members:
   :undoc-members:
   :show-inheritance:

   Summary of test execution results across all scenarios and personas.

Enums
~~~~~

.. autoclass:: core.test_executor.TestStatus
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: core.test_executor.ValidationResult
   :members:
   :undoc-members:
   :show-inheritance:

Scenario Generator
------------------

.. automodule:: core.scenario_generator
   :members:
   :undoc-members:
   :show-inheritance:

ScenarioGenerator
~~~~~~~~~~~~~~~~~

.. autoclass:: core.scenario_generator.ScenarioGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Generates test scenarios based on application analysis and persona requirements.

   **Example Usage:**

   .. code-block:: python

      from core.scenario_generator import ScenarioGenerator, ScenarioType
      from core.personas import PersonaManager

      generator = ScenarioGenerator()
      persona_manager = PersonaManager()

      # Get personas for testing
      personas = persona_manager.get_testing_matrix()

      # Generate scenarios
      scenarios = generator.generate_scenarios_for_personas(
          personas=personas,
          app_analysis=app_analysis,
          scenario_types=[ScenarioType.FUNCTIONAL, ScenarioType.SECURITY]
      )

TestScenario
~~~~~~~~~~~~

.. autoclass:: core.scenario_generator.TestScenario
   :members:
   :undoc-members:
   :show-inheritance:

   Represents a single test scenario with steps, expectations, and validation criteria.

TestStep
~~~~~~~~

.. autoclass:: core.scenario_generator.TestStep
   :members:
   :undoc-members:
   :show-inheritance:

   Represents a single step within a test scenario.

Enums
~~~~~

.. autoclass:: core.scenario_generator.ScenarioType
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: core.scenario_generator.InterfaceType
   :members:
   :undoc-members:
   :show-inheritance:

Report Generator
----------------

.. automodule:: core.report_generator
   :members:
   :undoc-members:
   :show-inheritance:

ReportGenerator
~~~~~~~~~~~~~~~

.. autoclass:: core.report_generator.ReportGenerator
   :members:
   :undoc-members:
   :show-inheritance:

   Generates comprehensive HTML and JSON reports from test execution results.

   **Example Usage:**

   .. code-block:: python

      from core.report_generator import ReportGenerator

      generator = ReportGenerator()

      # Generate HTML report
      await generator.generate_comprehensive_report_async(
          report_data=test_data,
          output_file=Path("./report.html")
      )

      # Generate JSON report
      await generator.generate_json_report_async(
          report_data=test_data,
          output_file=Path("./results.json")
      )

Utility Functions
-----------------

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: core.test_executor.AutonomousQATester._load_default_config

   Loads default configuration for the testing framework.

App Discovery
~~~~~~~~~~~~~

.. autofunction:: core.test_executor.AutonomousQATester.discover_app

   Discovers application structure and capabilities through static analysis.

Validation Functions
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: core.test_executor.AutonomousQATester._validate_test_results

   Validates test results against expected outcomes and persona capabilities.

Constants
---------

Default Configuration
~~~~~~~~~~~~~~~~~~~~~

.. data:: DEFAULT_CONFIG

   Default configuration dictionary used by the testing framework:

   .. code-block:: python

      DEFAULT_CONFIG = {
          "discovery": {
              "analyze_code": True,
              "analyze_docs": True,
              "analyze_tests": True,
              "extract_permissions": True,
              "detect_interfaces": True
          },
          "testing": {
              "max_concurrent_tests": 3,
              "test_timeout_minutes": 10,
              "retry_failed_tests": True,
              "skip_slow_tests": False
          },
          "llm": {
              "use_consensus": True,
              "max_providers": 2,
              "analysis_timeout_seconds": 30
          },
          "reporting": {
              "generate_html": True,
              "generate_json": True,
              "include_llm_responses": True,
              "confidence_threshold": 70.0
          }
      }

Performance Metrics
~~~~~~~~~~~~~~~~~~~

.. data:: PERFORMANCE_TARGETS

   Target performance metrics for different application types:

   .. code-block:: python

      PERFORMANCE_TARGETS = {
          "small_app": {
              "discovery_time": 0.1,    # seconds
              "scenario_generation": 0.05,
              "test_execution": 1.0
          },
          "medium_app": {
              "discovery_time": 0.5,
              "scenario_generation": 0.2,
              "test_execution": 5.0
          },
          "large_app": {
              "discovery_time": 2.0,
              "scenario_generation": 1.0,
              "test_execution": 20.0
          }
      }

Error Handling
--------------

Exception Classes
~~~~~~~~~~~~~~~~~

.. autoexception:: core.test_executor.TestExecutionError

   Raised when test execution fails due to system errors.

.. autoexception:: core.test_executor.ConfigurationError

   Raised when configuration is invalid or missing required parameters.

.. autoexception:: core.test_executor.AppDiscoveryError

   Raised when application discovery fails.

Type Definitions
----------------

Type Aliases
~~~~~~~~~~~~

.. data:: AppAnalysis
   :type: Dict[str, Any]

   Dictionary containing application analysis results.

.. data:: PersonaList
   :type: List[Persona]

   List of persona objects for testing.

.. data:: ScenarioList
   :type: List[TestScenario]

   List of test scenario objects.

.. data:: TestResults
   :type: List[TestResult]

   List of test result objects.

Protocol Definitions
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: core.test_executor.TestExecutorProtocol
   :members:
   :undoc-members:
   :show-inheritance:

   Protocol defining the interface for test execution components.

.. autoclass:: core.test_executor.ReportGeneratorProtocol
   :members:
   :undoc-members:
   :show-inheritance:

   Protocol defining the interface for report generation components.
