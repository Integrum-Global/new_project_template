# Initial Instructions for Claude Code

1. Explain what we want to do, at a very high level.
2. Do not tell it your implementation or technical details.
3. Keep what you have in mind to yourself, let Claude Code build the overall frame first.
4. Look at the broad picture of what Claude Code presented and debate with it.
   - Refrain from diving straight into the solution or your idea.
   - Present the challenges from a solutions, users, or system perspective.
   - Ask it for solution
5. Iterate and iterate until you are satisfied with the frame.
6. Ask Claude Code to log it into adr, as much details as it can, and present the implementation plan.
7. Do the same with implementation plan and keep iterating.
8. Ask Claude Code to produce an extremely detailed todo list and log it into todos/.
9. Implement and always ask

# Example instructions:
## What this project is about?
1. (After debating with Claude Code, I asked it to rewrite into PROJECT_WRITEUP.md)

## Use-Case Design for Project
1. Look at our target repository at <local repository path>. (--add-dir to this consolde)
2. I want you to think deeply, as a user, about:
   - all the end to end workflows that the user will take
   - how our middleware should facilitate the storage, retrieval, modification of these custom workflows, custom nodes, custom runtime etc.
3. Some of the use-cases that I can think of:
   - Users use the LLM chat, and the coding llm will:
     - look through our sdk-users and then create and test workflows
     - make sure its working, and then similarly store it for later re-use
   - Users will consult an auto-populated list of built-in nodes, and have access to their custom workflows and runtimes
   - Users can create, manage and run gateways from the UI.
     - Which means that the solution should have deployment functions as well.
     - We also need to be able to present an intuitive way to understanding our extensive api/cli/mcp gateways/hybrid gateways for users.
   - Users can connect external frontend apps through our interface:
     - social media apps (e.g. Whatspp, Telegram, Line) can be created within the solution as a node
     - jira/discord/sap and other enterprise/productivity apps can be created within the solution as nodes and served through our MCP gateway
     - Give a list of frontend endpoints and create the gateway with required nodes to serve.
   - Users can track and monitor via a dashboard interface on all running workflows through gateways.
4. These are some use-cases that I can think of but I'm sure you can come up with an even more extensive list.

## Infrastructure Needs

1. Suggest the best way to handle the storage and retrieval of custom nodes and workflows and runtimes between the solution and frontend
2. Currently, custom nodes and workflows are created via coding LLM that writes directly into codebase
3. If we have a drag and drop and LLM chat interface where users create their own custom implementation:
   - we may need a translation (json, yaml) mechanism for storage and retrieval between the solution and the frontend
   - we will thus need some kind of a loader mechanism to operationalize it within the codebase.
   - Same goes for the runtimes and gateways.
4. This solution is intended to run at large enterprises (>20000 employees with potentially thousands of concurrent access.
   - Suggest how should we design the infrastructure (kubernetes?) to support this scale using the best enterprise standards.

## Start Thinking from User Perspective
1. Given the above instructions, I need you to first adopt a user/UI perspective, then work backwards to the codebase and technology.
2. Please give me your deep thoughts and we can discuss further.

# Verify the implementation and then document it (this are plans not adrs - see 02 - implementation.md)
1. Document all of the above into docs/ and please break it up into different documents categorized in a way that's easy for Claude Code to navigate.
