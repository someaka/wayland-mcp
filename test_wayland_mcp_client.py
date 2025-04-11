import asyncio
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Path to the uvx MCP server command
    server_params = StdioServerParameters(
        command="uvx",
        args=["wayland-mcp"],
        env=os.environ.copy()
    )

    async with AsyncExitStack() as stack:
        stdio_transport = await stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        session = await stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()

        # List tools
        response = await session.list_tools()
        print("Available tools:", [tool.name for tool in response.tools])

        # Call the capture_screenshot tool
        result = await session.call_tool("capture_screenshot", {})
        print("Screenshot result:", result)

asyncio.run(main())