import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()


class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def connect_to_server(self, server_script_path: str):
        """Connect to MCP server

        Args:
            server_script_path: Path to server script    
        """

        # Only expecting python as my whole project is in python
        if not server_script_path.endswith(".py"):
            raise ValueError("Server script must be .py")

        command = f"{os.getcwd()}\..\weather\.venv\Scripts\python.exe"
        if not os.path.exists(command):
            raise ValueError("Incorrect path")

        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:",
              [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available tools

        Args:
            query: User's query
        """
        messages = [{
            "role": "user",
            "content": query
        }]

        response = await self.session.list_tools()
        available_tools = [{
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema
        } for tool in response.tools]

        response = await self.openai.responses.create(
            model="gpt-5.4-nano",
            tools=available_tools,
            input=messages,
        )

        final_text = []

        # assistant_message_context = []
        messages += response.output
        for content in response.output:
            if content.type == "function_call":
                tool_name = content.name
                try:
                    tool_args = json.loads(content.arguments)
                except (json.JSONDecodeError, KeyError) as e:
                    messages.append({
                        "type": "function_call_output",
                        "call_id": content.call_id,
                        "output": f" Failed, error with arguments - {e}"
                    })
                else:
                    # Execute tool call
                    result = await self.session.call_tool(tool_name, tool_args)
                    final_text.append(
                        f"[Calling tool{tool_name} with args {tool_args}]")

                    # assistant_message_context.append(content)
                    messages.append({
                        "type": "function_call_output",
                        "call_id": content.call_id,
                        "output": result.content[0].text
                    })

        # Next response from OpenAi
        response = await self.openai.responses.create(
            model="gpt-5.4-nano",
            tools=available_tools,
            input=messages,
        )

        final_text.append(response.output_text)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()

    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
