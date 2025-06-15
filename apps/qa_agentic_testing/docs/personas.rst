Persona System
==============

The QA Agentic Testing framework includes a comprehensive persona system with **27 built-in personas** covering common enterprise roles and **4 industry-specific templates** for specialized testing scenarios.

Built-in Enterprise Personas
-----------------------------

Administrative Personas
~~~~~~~~~~~~~~~~~~~~~~~~

**System Admin (Alice Admin)**
   * **Role**: System Administrator
   * **Permissions**: Full system access (*)
   * **Focus**: Security, functionality, performance, audit
   * **Success Rate**: 100.0%
   * **Use Case**: Complete system validation and security testing

**Security Officer (Sarah Security)**
   * **Role**: Security Officer
   * **Permissions**: user:read, role:read, audit:read, security:*
   * **Focus**: Security, audit, compliance
   * **Success Rate**: 75.0%
   * **Use Case**: Security validation and compliance checking

**Manager (Mark Manager)**
   * **Role**: Department Manager
   * **Permissions**: user:read, user:update, role:read, audit:read:own_department
   * **Focus**: Functionality, permissions, usability
   * **Success Rate**: 60.0%
   * **Use Case**: Department-level operations and team management

Business User Personas
~~~~~~~~~~~~~~~~~~~~~~~

**Analyst (Anna Analyst)**
   * **Role**: Business Analyst
   * **Permissions**: data:read, reports:generate, export:data
   * **Focus**: Functionality, performance, data accuracy
   * **Success Rate**: 80.0%
   * **Use Case**: Data analysis, reporting, and business intelligence

**Regular User (Rachel Regular)**
   * **Role**: Regular User
   * **Permissions**: user:read:self, user:update:self, data:read:own
   * **Focus**: Usability, functionality, accessibility
   * **Success Rate**: 90.0%
   * **Use Case**: Standard workflows and daily operations

**New User (Nancy Newbie)**
   * **Role**: New User
   * **Permissions**: user:read:self, onboarding:access
   * **Focus**: Usability, onboarding, accessibility, help system
   * **Success Rate**: 70.0%
   * **Use Case**: Onboarding experience and learning curve testing

**Power User (Paul Power)**
   * **Role**: Power User
   * **Permissions**: user:*:self, advanced:features, integration:api
   * **Focus**: Advanced features, performance, integration, automation
   * **Success Rate**: 95.0%
   * **Use Case**: Advanced feature usage and productivity optimization

Industry-Specific Persona Templates
------------------------------------

Financial Services (5 Personas)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Compliance Officer (Catherine Compliance)**
   * **Role**: Financial Compliance Officer
   * **Permissions**: audit:*, compliance:*, risk:assess, transactions:review
   * **Focus**: Security, compliance, audit, functionality
   * **Success Rate**: 95.0%
   * **Specialization**: Regulatory validation, risk assessment

**Trading Desk User (Thomas Trader)**
   * **Role**: Trading Desk Operator
   * **Permissions**: trading:execute, market:read, portfolio:read, orders:*
   * **Focus**: Performance, functionality, real-time, accuracy
   * **Success Rate**: 98.0%
   * **Specialization**: High-frequency operations, real-time performance

**Risk Analyst (Rebecca Risk)**
   * **Role**: Risk Management Analyst
   * **Permissions**: risk:*, models:access, data:analyze, scenarios:run
   * **Focus**: Data accuracy, performance, functionality, validation
   * **Success Rate**: 90.0%
   * **Specialization**: Risk calculations, stress testing scenarios

**Portfolio Manager (Patrick Portfolio)**
   * **Role**: Senior Portfolio Manager
   * **Permissions**: portfolio:*, trading:approve, risk:override, clients:manage
   * **Focus**: Functionality, security, performance, reporting
   * **Success Rate**: 92.0%
   * **Specialization**: Investment strategies, client relationships

**Operations Specialist (Oliver Operations)**
   * **Role**: Financial Operations Specialist
   * **Permissions**: settlements:process, reconciliation:perform, data:validate
   * **Focus**: Functionality, data accuracy, workflows, reliability
   * **Success Rate**: 88.0%
   * **Specialization**: Trade settlements, data reconciliation

Healthcare (5 Personas)
~~~~~~~~~~~~~~~~~~~~~~~~

**Clinical User (Dr. Clara Clinical)**
   * **Role**: Clinical Physician
   * **Permissions**: patient:read, patient:update, medical_records:access
   * **Focus**: Functionality, security, privacy, accuracy
   * **Success Rate**: 95.0%
   * **Specialization**: Patient care, medical record access, HIPAA compliance

**Nurse Practitioner (Nancy Nurse)**
   * **Role**: Registered Nurse Practitioner
   * **Permissions**: patient:read, vitals:record, medications:administer
   * **Focus**: Functionality, real-time, usability, reliability
   * **Success Rate**: 92.0%
   * **Specialization**: Patient monitoring, care coordination

**Hospital Administrator (Harold Admin)**
   * **Role**: Hospital Administrator
   * **Permissions**: users:manage, departments:oversee, reports:access
   * **Focus**: Functionality, reporting, security, performance
   * **Success Rate**: 90.0%
   * **Specialization**: Hospital operations, compliance management

**Privacy Officer (Patricia Privacy)**
   * **Role**: HIPAA Privacy Officer
   * **Permissions**: audit:access, privacy:monitor, breaches:investigate
   * **Focus**: Security, audit, compliance, privacy
   * **Success Rate**: 98.0%
   * **Specialization**: HIPAA compliance, privacy protection

**Lab Technician (Laura Lab)**
   * **Role**: Laboratory Technician
   * **Permissions**: lab_orders:view, results:enter, specimens:track
   * **Focus**: Accuracy, functionality, workflows, quality
   * **Success Rate**: 94.0%
   * **Specialization**: Lab processes, quality control

Manufacturing (5 Personas)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Plant Manager (Marcus Manager)**
   * **Role**: Manufacturing Plant Manager
   * **Permissions**: operations:oversee, production:schedule, safety:monitor
   * **Focus**: Functionality, performance, reporting, security
   * **Success Rate**: 93.0%
   * **Specialization**: Production optimization, safety compliance

**Quality Inspector (Quincy Quality)**
   * **Role**: Quality Control Inspector
   * **Permissions**: quality:inspect, defects:report, standards:enforce
   * **Focus**: Accuracy, functionality, audit, validation
   * **Success Rate**: 96.0%
   * **Specialization**: Quality assurance, defect tracking

**Maintenance Technician (Mike Maintenance)**
   * **Role**: Equipment Maintenance Technician
   * **Permissions**: equipment:access, maintenance:schedule, repairs:perform
   * **Focus**: Functionality, reliability, workflows, usability
   * **Success Rate**: 89.0%
   * **Specialization**: Equipment maintenance, preventive care

**Production Supervisor (Susan Supervisor)**
   * **Role**: Production Line Supervisor
   * **Permissions**: line:monitor, workers:supervise, targets:track
   * **Focus**: Functionality, real-time, performance, usability
   * **Success Rate**: 91.0%
   * **Specialization**: Production monitoring, team coordination

**Safety Coordinator (Samuel Safety)**
   * **Role**: Workplace Safety Coordinator
   * **Permissions**: safety:monitor, incidents:investigate, training:manage
   * **Focus**: Compliance, security, audit, functionality
   * **Success Rate**: 97.0%
   * **Specialization**: Safety compliance, incident investigation

Retail/E-commerce (5 Personas)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Customer Service Rep (Carla Customer)**
   * **Role**: Customer Service Representative
   * **Permissions**: orders:view, customers:assist, returns:process
   * **Focus**: Functionality, usability, workflows, performance
   * **Success Rate**: 88.0%
   * **Specialization**: Customer support, order management

**Inventory Manager (Ian Inventory)**
   * **Role**: Inventory Management Specialist
   * **Permissions**: inventory:manage, stock:monitor, orders:place
   * **Focus**: Functionality, data accuracy, performance, reporting
   * **Success Rate**: 92.0%
   * **Specialization**: Stock management, demand forecasting

**Marketing Analyst (Madison Marketing)**
   * **Role**: Digital Marketing Analyst
   * **Permissions**: campaigns:create, analytics:access, customers:segment
   * **Focus**: Functionality, analytics, performance, integration
   * **Success Rate**: 85.0%
   * **Specialization**: Campaign optimization, customer analytics

**Warehouse Operator (William Warehouse)**
   * **Role**: Warehouse Operations Specialist
   * **Permissions**: orders:fulfill, inventory:track, shipping:manage
   * **Focus**: Functionality, accuracy, workflows, usability
   * **Success Rate**: 94.0%
   * **Specialization**: Order fulfillment, warehouse efficiency

**Fraud Analyst (Francine Fraud)**
   * **Role**: E-commerce Fraud Analyst
   * **Permissions**: transactions:review, fraud:investigate, accounts:suspend
   * **Focus**: Security, fraud detection, analytics, performance
   * **Success Rate**: 96.0%
   * **Specialization**: Fraud detection, transaction security

Using Personas
--------------

Auto-Generation from Your App
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Automatic persona discovery
   qa-test /path/to/your/app --discover-personas

   # The system analyzes your app and creates personas based on:
   # ✓ Discovered permissions (user:create, admin:delete, etc.)
   # ✓ Role definitions in code
   # ✓ API endpoint access patterns
   # ✓ UI access levels and workflows

Industry-Specific Loading
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Load healthcare personas for medical applications
   qa-test /path/to/your/app --industry healthcare

   # Load financial services personas for banking/trading apps
   qa-test /path/to/your/app --industry financial_services

   # Load manufacturing personas for industrial applications
   qa-test /path/to/your/app --industry manufacturing

   # Load retail personas for e-commerce applications
   qa-test /path/to/your/app --industry retail_ecommerce

Custom Persona Creation
~~~~~~~~~~~~~~~~~~~~~~~

**Interactive Wizard:**

.. code-block:: bash

   # Create custom personas for your domain
   qa-test personas create --interactive

**JSON Template:**

.. code-block:: json

   {
     "key": "finance_approver",
     "name": "Finance Approver",
     "role": "Financial Operations Manager",
     "permissions": ["invoice:approve", "budget:read", "report:generate"],
     "goals": ["Approve financial transactions", "Monitor budget compliance"],
     "behavior_style": "Detail-oriented, risk-averse, compliance-focused",
     "typical_actions": ["Review invoices", "Generate financial reports"],
     "expected_success_rate": 90.0,
     "test_focus": ["functionality", "security", "compliance"]
   }

**Load Custom Personas:**

.. code-block:: bash

   # Use custom personas file
   qa-test /path/to/your/app --personas ./custom-personas.json

CLI Commands
------------

List Available Personas
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Show all personas
   qa-test personas list

   # Show specific industry
   qa-test personas list --industry healthcare

   # List available industries
   qa-test personas industries

Create Custom Personas
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Interactive creation wizard
   qa-test personas create --interactive

   # Save to file
   qa-test personas create --interactive --file ./my-personas.json

Best Practices
--------------

Selecting Personas for Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Match Industry Context**: Use industry-specific personas when available
2. **Cover Permission Levels**: Include admin, manager, and regular user personas
3. **Test Edge Cases**: Include new users and power users for comprehensive coverage
4. **Security Focus**: Always include security-focused personas for sensitive applications

Persona Configuration Tips
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Expected Success Rates**: Set realistic expectations based on permission levels
2. **Test Focus Areas**: Specify relevant focus areas for targeted testing
3. **Behavior Styles**: Define realistic behavior patterns for accurate testing
4. **Permission Mapping**: Ensure permissions align with actual application capabilities

Integration Examples
~~~~~~~~~~~~~~~~~~~~

See the :doc:`examples/user_management` section for detailed examples of persona usage in real applications.
