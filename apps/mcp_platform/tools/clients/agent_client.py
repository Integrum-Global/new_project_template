#!/usr/bin/env python3
"""Agent MCP Client - LLM Agent that uses MCP tools."""

import asyncio
import logging
from typing import Any, Dict, List

from kailash.core import LocalRuntime, WorkflowBuilder
from kailash.nodes.ai import LLMAgentNode

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MCPAgentClient:
    """LLM Agent that can discover and use MCP tools."""

    def __init__(self, mcp_servers: List[str], model: str = "gpt-4"):
        """Initialize agent with MCP servers."""
        self.runtime = LocalRuntime()
        self.mcp_servers = mcp_servers
        self.model = model
        self.agent = None
        self.workflow = None

    def create_agent(self) -> LLMAgentNode:
        """Create LLM agent with MCP integration."""
        agent = LLMAgentNode(
            name="mcp_assistant",
            llm_config={"model": self.model, "temperature": 0.7, "max_tokens": 2000},
            mcp_servers=self.mcp_servers,
            enable_mcp=True,
            system_prompt="""You are a helpful assistant with access to MCP tools.

When the user asks you to perform calculations, data processing, or other operations,
check which tools are available and use them appropriately.

Always explain what you're doing and show the results clearly.""",
        )

        return agent

    def create_workflow(self) -> Any:
        """Create workflow with MCP-enabled agent."""
        builder = WorkflowBuilder("mcp-agent-workflow")

        # Add MCP-enabled agent
        builder.add_node(
            "agent",
            "LLMAgentNode",
            config={
                "llm_config": {
                    "model": self.model,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
                "mcp_servers": self.mcp_servers,
                "enable_mcp": True,
                "system_prompt": "You are a helpful assistant with MCP tool access.",
            },
        )

        # Add a result processor
        builder.add_node(
            "formatter",
            "PythonCodeNode",
            config={
                "code": """
def process(data):
    response = data.get("response", {})

    # Format the response nicely
    formatted = {
        "assistant_response": response.get("content", ""),
        "tools_used": response.get("tools_used", []),
        "success": True
    }

    return formatted
"""
            },
        )

        # Connect nodes
        builder.add_connection("agent", "response", "formatter", "data")

        return builder.build()

    async def chat(self, message: str) -> Dict[str, Any]:
        """Send a message to the agent and get response."""
        if not self.agent:
            self.agent = self.create_agent()

        # Process message
        input_data = {"messages": [{"role": "user", "content": message}]}

        try:
            result = await self.agent.process(input_data)
            return result
        except Exception as e:
            logger.error(f"Agent processing failed: {e}")
            return {
                "response": {"content": f"Error: {str(e)}"},
                "tools_used": [],
                "error": str(e),
            }

    async def workflow_chat(self, message: str) -> Dict[str, Any]:
        """Use workflow for chat processing."""
        if not self.workflow:
            self.workflow = self.create_workflow()

        # Execute workflow
        input_data = {"messages": [{"role": "user", "content": message}]}

        try:
            result = await self.runtime.execute_workflow(self.workflow, input_data)
            return result.get("formatter", {})
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {"error": str(e)}

    async def demo_tool_discovery(self):
        """Demonstrate agent discovering and using tools."""
        logger.info("\n=== Tool Discovery Demo ===")

        # Ask agent to list available tools
        response = await self.chat(
            "What tools do you have available? Please list them with descriptions."
        )
        logger.info(f"Agent response:\n{response['response']['content']}")

    async def demo_calculations(self):
        """Demonstrate mathematical calculations."""
        logger.info("\n=== Calculations Demo ===")

        queries = [
            "Calculate 25 * 37",
            "What is the factorial of 7?",
            "Generate the first 15 Fibonacci numbers",
            "Calculate the mean, median, and standard deviation of these numbers: 23, 45, 67, 12, 89, 34, 56",
        ]

        for query in queries:
            logger.info(f"\nUser: {query}")
            response = await self.chat(query)
            logger.info(f"Assistant: {response['response']['content']}")
            if response.get("tools_used"):
                logger.info(f"Tools used: {response['tools_used']}")

    async def demo_data_processing(self):
        """Demonstrate data processing capabilities."""
        logger.info("\n=== Data Processing Demo ===")

        # JSON parsing
        response = await self.chat(
            'Parse this JSON and tell me what it contains: {"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}'
        )
        logger.info(f"JSON parsing result:\n{response['response']['content']}")

        # Data transformation
        response = await self.chat(
            """I have this data: [{"name": "john", "score": 85}, {"name": "jane", "score": 92}]
            Can you transform it to uppercase the names and sort by score descending?"""
        )
        logger.info(f"Data transformation result:\n{response['response']['content']}")

    async def demo_utility_operations(self):
        """Demonstrate utility operations."""
        logger.info("\n=== Utility Operations Demo ===")

        # Current time
        response = await self.chat("What's the current date and time?")
        logger.info(f"Time query: {response['response']['content']}")

        # UUID generation
        response = await self.chat("Generate a new UUID for me")
        logger.info(f"UUID generation: {response['response']['content']}")

        # Hashing
        response = await self.chat(
            "Calculate the SHA256 hash of the text 'Hello MCP World'"
        )
        logger.info(f"Hash calculation: {response['response']['content']}")

    async def demo_complex_tasks(self):
        """Demonstrate complex multi-tool tasks."""
        logger.info("\n=== Complex Tasks Demo ===")

        # Complex calculation task
        response = await self.chat(
            """I need to:
            1. Calculate the factorial of 6
            2. Generate 10 Fibonacci numbers
            3. Find the sum of the Fibonacci numbers
            4. Multiply the factorial by this sum
            Please show me each step."""
        )
        logger.info(f"Complex calculation:\n{response['response']['content']}")

        # Data analysis task
        response = await self.chat(
            """Analyze this sales data and give me insights:
            [{"month": "Jan", "sales": 45000}, {"month": "Feb", "sales": 52000},
             {"month": "Mar", "sales": 48000}, {"month": "Apr", "sales": 61000}]

            Calculate the total, average, and identify the best month."""
        )
        logger.info(f"Data analysis:\n{response['response']['content']}")


async def interactive_agent_mode(agent: MCPAgentClient):
    """Run agent in interactive chat mode."""
    logger.info("\n=== Interactive Agent Mode ===")
    logger.info("Chat with the MCP-enabled assistant. Type 'quit' to exit.")
    logger.info("The assistant has access to math, data, file, and utility tools.")

    conversation_history = []

    while True:
        try:
            # Get user input
            user_message = input("\nYou: ").strip()

            if user_message.lower() == "quit":
                break

            if user_message.lower() == "history":
                print("\n=== Conversation History ===")
                for msg in conversation_history:
                    print(f"{msg['role']}: {msg['content'][:100]}...")
                continue

            if user_message.lower() == "clear":
                conversation_history = []
                print("Conversation history cleared.")
                continue

            # Add to history
            conversation_history.append({"role": "user", "content": user_message})

            # Get agent response
            print("\nAssistant: ", end="", flush=True)
            response = await agent.chat(user_message)

            assistant_message = response["response"]["content"]
            print(assistant_message)

            # Show tools used if any
            if response.get("tools_used"):
                print(f"\n[Tools used: {', '.join(response['tools_used'])}]")

            # Add to history
            conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}")


async def main():
    """Run the MCP agent client demo."""
    import sys

    # Get MCP server URLs from command line or use default
    if len(sys.argv) > 1:
        mcp_servers = sys.argv[1:]
    else:
        mcp_servers = ["mcp://localhost:8080"]

    logger.info(f"Connecting to MCP servers: {mcp_servers}")

    # Create agent client
    agent = MCPAgentClient(mcp_servers=mcp_servers)

    try:
        # Run demos
        await agent.demo_tool_discovery()
        await agent.demo_calculations()
        await agent.demo_data_processing()
        await agent.demo_utility_operations()
        await agent.demo_complex_tasks()

        # Interactive mode
        await interactive_agent_mode(agent)

    except Exception as e:
        logger.error(f"Agent client error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
