# Implementation Instructions

## Organize the Project Structure (Optional)
1. Inspect the src/ directory structure and suggest how best we should structure the project directories, so that we can implement all that you have documented.

## Document first before implementing
1. Create separate ADRs (in solution's adr/) for each of the decisions we make.
2. Then create a comprehensive list of todos (in solution's todos/) that we need to implement.
3. You should consider the existing practice in this repository (kailash_python_sdk) and adjust your implementation accordingly.

# Implementing the solution
1. Proceed with the implementation.
   - Use 100% kailash sdk components (the latest version installed from pypi) and consult sdk-users/ every time.
   - Do not create new code without checking it against the existing SDK components.
   - Do not assume any new functionality without verifying it against the user flow specifications.
   - If you meet any errors in the SDK, check sdk-users/ because we would have resolved it already.

# Testing the kailash implementation
1. I want to perform extensive testing on your implementation.
2. We should have 3 kinds of tests:
   - **Unit tests**: For each component, we should have unit tests that cover the functionality.
   - **Integration tests**: For the entire workflow, we should have integration tests that ensure everything works together as expected.
   - **User flow tests**: For each user flow, we should have user flow tests that ensure the user experience is smooth and intuitive.
     - First, generate all the different user personas and user flows based on the documentation you have created.
     - Then, document them into solution's docs/user_flows/ with a separate folder for each user flow.
     - Next, for each user flow, generate the test codes in solution's tests/user_flows/ with a separate folder for each user flow.
     - Have a md in each user flow folder that explains the user flow (referencing docs/user_flows/*) and the test cases.
   - Finally, run the tests and ensure that everything is working as expected.
3. As you correct the codes, ensure the following:
   - Use 100% kailash SDK components (the latest version installed from pypi), and that you have consulted sdk-users/ for any doubts.
   - This is a live production so do not use any mocks.
     - The use of simplified examples or tests is allowed for your learning, and must be re-implemented into the original production examples and tests.
     - Launch the dockers/kubernetes and run the tests as a live system. If it fails, then you need to fix the code until it passes.
     - Use the existing ollama for your tests.
4. From the user flows, extract, generalize, and optimize them into highly efficient reusable nodes and workflows.
   - Nodes go into the solution's nodes/ and workflows go into the solution's workflows/.
   - These nodes and workflows are what is running in production throughout the system (gateways, servers), so they must be optimized for performance and reliability.
   - Ensure that the other service and infrastructure components are also optimized for performance and reliability.

# Checking tests completeness
1. Lets resolve testing issues or gaps, if any. I need it to be of the best production quality.
2. Lets have integration, e2e, and user flows tests that are more demanding and real-world in nature.
3. For the tests, please use our docker implementation, and real data, processes, responses.
4. Use our ollama to generate data or create LLMAgents freely.

# Updating the documentation
1. Please update all the documentation and references in details. We should indicate what tests were performed, and what were the results.
   - This includes the architecture decisions, todos, user guides, developer guides, and any other relevant documentation.
   - Ensure that the documentation is clear, concise, and easy to follow for both developers and users.
2. Ensure that your codes and usages are correct.
3. update the master todo list and the todos/ in details.

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
