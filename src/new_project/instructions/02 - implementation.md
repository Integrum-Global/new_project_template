# Implementation Instructions

## Organize the Project Structure (Optional)
1. Inspect the src/ directory structure and suggest how best we should structure the project directories, so that we can implement all that you have documented.

## Document first before implementing
1. Create separate ADRs (in solution's adr/) for each of the decisions we make.
2. Then create a comprehensive list of todos (in solution's todos/) that we need to implement.
3. The local todo management system is two-tiered: Repo level todos are in root and module level todos are in their respective src/ sub-directories.
   - Start with updating the master list (`000-master.md`)
   - Look through the entire file thoroughly and add the new todos.
   - Ensure that each todo's details are captured in `todos/active`.

# Implementing the solution
1. Proceed with the implementation.
   - Use 100% kailash sdk components (the latest version installed from pypi) and consult sdk-users/ every time.
   - Do not create new code without checking it against the existing SDK components.
   - Do not assume any new functionality without verifying it against the user flow specifications.
   - If you meet any errors in the SDK, check sdk-users/ because we would have resolved it already.
2. After each todo item (feature/fix), please test your implementation thoroughly.
   - Do not write new tests without checking that existing ones can be modified to include them.
   - We should have 3 kinds of tests which MUST follow the strategy in `sdk-users/testing/regression-testing-strategy.md`, and policy in `sdk-users/testing/test-organization-policy.md`:
      - **Unit tests (Tier 1)**
        - For each component, we should have unit tests that cover the functionality. 
        - Can use mocks, must be fast (<1s per test), no external dependencies, no sleep.
      - **Integration tests (Tier 2)**
        - For each component, we should have integration tests to ensure that it works together with the system.
        - NO MOCKING, must use real Docker services
      - **User flow/e2e tests (Tier 3)**
        - First, generate all the different user personas and user flows based on the documentation you have created.
        - Then, document them into solution's docs/user_flows/ with a separate folder for each user flow.
        - Next, for each user flow, generate the test codes in solution's tests/user_flows/ with a separate folder for each user flow. 
        - Have a md in each user flow folder that explains the user flow (referencing docs/user_flows/*) and the test cases.
        - NO MOCKING, complete scenarios with real infrastructure
     - If you find any existing tests with policy violations, please fix them immediately.
3. DO NOT create new docker containers or images before checking that the docker for this repository exists.
   - **IMPORTANT**: You MUST have a `tests/.docker-ports.lock` file that locks in the specific ports for that project.
   - If Docker infrastructure doesn't exist yet, follow these steps:
     a. Run `python tests/utils/setup_local_docker.py --check-ports` to check for conflicts
     b. If conflicts exist, use `--custom-base-port` flag to set a different port range
     c. The setup script will automatically create a `.docker-ports.lock` file with your allocated ports
   - The dynamic port allocation formula ensures each project gets unique ports:
     ```
     base_port = 5000 + (hash(project_name) % 1000) * 10
     ```
   - Port assignments per service:
     - PostgreSQL: base_port + 0
     - Redis: base_port + 1
     - Ollama: base_port + 2
     - MySQL: base_port + 3
     - MongoDB: base_port + 4
   - Use the docker-compose approach outlined in `tests/utils/CLAUDE.md`.
   - The setup script will register ports in `~/.docker_port_registry` for team coordination.
   - Update this setup and the CLAUDE.md in `tests/utils` if needed.
4. Please update the docs every time a feature is done and fully tested. Ensure that wrong usages are corrected, and that the guides are clear and concise.
5. Do not stop until you are done with the implementation.

# Testing the kailash implementation
1. I want to perform extensive testing on your implementation.
   - Do not write new tests without checking that existing ones can be modified to include them.
   - We should have 3 kinds of tests which MUST follow the strategy in `sdk-users/testing/regression-testing-strategy.md`, and policy in `sdk-users/testing/test-organization-policy.md`:
      - **Unit tests (Tier 1)**
        - For each component, we should have unit tests that cover the functionality. 
        - Can use mocks, must be fast (<1s per test), no external dependencies, no sleep.
      - **Integration tests (Tier 2)**
        - For each component, we should have integration tests to ensure that it works together with the system.
        - NO MOCKING, must use real Docker services
      - **User flow/e2e tests (Tier 3)**
        - First, generate all the different user personas and user flows based on the documentation you have created.
        - Then, document them into solution's docs/user_flows/ with a separate folder for each user flow.
        - Next, for each user flow, generate the test codes in solution's tests/user_flows/ with a separate folder for each user flow. 
        - Have a md in each user flow folder that explains the user flow (referencing docs/user_flows/*) and the test cases.
        - NO MOCKING, complete scenarios with real infrastructure
     - If you find any existing tests with policy violations, please fix them immediately.
2. Always use the docker implementation in `tests/utils`, and real data, processes, responses.
   - Use our ollama to generate data or create LLMAgents freely.
   - DO NOT create new docker containers or images before checking that the docker for this repository exists.
3. As you correct the codes, ensure the following:
   - Use 100% kailash SDK components (the latest version installed from pypi), and that you have consulted sdk-users/ for any doubts.
   - This is a live production so do not use any mocks.
     - The use of simplified examples or tests is allowed for your learning, and must be re-implemented into the original production examples and tests.
     - Launch the dockers/kubernetes in `tests/utils` and run the tests as a live system. If it fails, then you need to fix the code until it passes.
     - Use the existing ollama for your tests.
4. From the user flows, extract, generalize, and optimize them into highly efficient reusable nodes and workflows.
   - Nodes go into the solution's nodes/ and workflows go into the solution's workflows/.
   - These nodes and workflows are what is running in production throughout the system (gateways, servers), so they must be optimized for performance and reliability.
   - Ensure that the other service and infrastructure components are also optimized for performance and reliability.
5. Please update the docs every time a feature is done and fully tested. Ensure that wrong usages are corrected, and that the guides are clear and concise.

# Checking tests completeness
1. Let's resolve testing issues or gaps, if any. I need it to be of the best production quality.
2. The regression testing strategy is in `sdk-users/testing/regression-testing-strategy.md`, and policy in `sdk-users/testing/test-organization-policy.md`.
3. Additional tests written MUST follow the policy in `sdk-users/testing/test-organization-policy.md`.
   - Do not write new tests without checking that existing ones can be modified to include them.
   - Ensure that the integration and e2e tests that are demanding and real-world in nature.
4. Always use the docker implementation in `tests/utils`, and real data, processes, responses.
   - Use our ollama to generate data or create LLMAgents freely.
   - DO NOT create new docker containers or images before checking that the docker for this repository exists.
5. Commit after each tier of tests is cleared.

# Updating the documentation
1. Please update all the documentation and references in details. We should indicate what tests were performed, and what were the results.
   - This includes the architecture decisions, todos, user guides, developer guides, and any other relevant documentation.
   - Ensure that the documentation is clear, concise, and easy to follow for both developers and users.
2. Ensure that your codes and usages are correct.   
3. update the master todo list and the todos/ in details.

# Updating the guidance system
1. Check the `CLAUDE.md` in root and other directories.
   - Check if we need to update the guidance system.
   - Ensure that only the absolute essentials are included.
   - Adopt a multi-step approach by using the existing `CLAUDE.md` network (root -> sdk-users/ -> specific guides).
     - Do not try to solve everything in one place, make use of the hierarchical documentation system.
   - Issue commands instead of explanations.
   - Ensure that your commands are sharp and precise, covering only critical pattterns that prevent immediate failure.
   - Run through the guidance flow yourself and ensure the following:
     - You can trace a complete path from basic patterns to advanced custom development.
     - Please maintain the concise, authoritative tone that respects context limits!

# Updating the todo management system
1. The local todo management system is two-tiered: Repo level todos are in root and module level todos are in their respective src/ sub-directories.
2. Start with updating the master list (`000-master.md`)
   - Look through the entire file thoroughly.
   - Add outstanding todos that are not yet implemented.
   - Update the status of existing todos.
   - Remove old completed entries that don't add context to outstanding todos.
   - Keep this file concise, lean, and easy to navigate.
3. Ensure that each todo's details are captured in
   - `todos/active` for outstanding todos.
   - `todos/completed` for completed todos.
   - move completed todos from `todos/active` to `todos/completed` with the date of completion.

# Full tests
1. Running all tests will take very long, let's clear Tier 1, then Tier 2, before clearing Tier 3 one at a time.
2. The regression testing strategy is in `sdk-users/testing/regression-testing-strategy.md`, and policy in `sdk-users/testing/test-organization-policy.md`.
3. Please use the docker implementation in `tests/utils`, and real data, processes, responses.
4. Always use the docker implementation in `tests/utils`, and real data, processes, responses.
   - Use our ollama to generate data or create LLMAgents freely.
   - DO NOT create new docker containers or images before checking that the docker for this repository exists.
5. Use our ollama to generate data or create LLMAgents freely.
6. For the tests, please use the docker implementation in `tests/utils`, and real data, processes, responses.
7. Additional tests written MUST follow the policy in 'sdk-users/testing/test-organization-policy.md'.
8. Do not write new tests without checking that existing ones can be modified to include them.
9. Please update the developer and user guides (inside `sdk-users/`).
   - Every time a feature is done and fully tested. 
   - Ensure that wrong usages are corrected
   - Ensure that guides are clear and concise.
10. Commit after each tier of tests is cleared.

# Integrating with frontend
1. Analyze docs/ in details. We need to ensure that the backend implementation aligns with the frontend specifications.
2. Create a mapping of the backend APIs to the frontend requirements, ensuring that all endpoints are covered.
3. Document the detailed architecture and flow of data between the backend and frontend in docs/integration/.
4. Document the architecture decisions made during this integration in adr/, that any discrepancies or additional requirements are specified
5. Populate the details into our todos.
6. Implement the necessary workflows, nodes, gateways, and other components to ensure the backend supports the frontend requirements.
   - Use 100% kailash sdk components (the latest version installed from pypi) and consult sdk-users/ every time.
   - Do not create new code without checking it against the existing SDK components.
   - Do not assume any new functionality without verifying it against the frontend specifications.
   - If you meet any errors in the SDK, check sdk-users/ because we would have resolved it already.
   - This is a live production so do not use any mocks.
     - The use of simplified examples or tests is allowed for your learning, and must be re-implemented into the original production examples and tests.
     - Launch the dockers/kubernetes and run the tests against the live system. If it fails, then you need to fix the code until it passes.
     - Use the existing ollama for your tests.

# Commit to github
1. Run black, isort with profile=black, and ruff.
2. Commit and push to github.
3. Issue PR
