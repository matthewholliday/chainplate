import asyncio
import os
from pydantic import AnyUrl
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.shared.context import RequestContext

class MCPService:
    def __init__(self, notion_token=None):
        self.notion_token = notion_token or "ntn_b89841075978RYBDlJ8XFoUZYblF89YINv7MystOtNW2Uo" #TODO - remove compromised token and use environment variable or config file for security
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@notionhq/notion-mcp-server"],
            env={"NOTION_TOKEN": self.notion_token},
        )

    async def list_tools(self):
        import json
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                result_lines = []
                for tool in tools.tools:
                    result_lines.append(f"Tool name: {tool.name}")
                    result_lines.append(f"Tool description: {tool.description}")
                    result_lines.append("Tool parameters:")
                    result_lines.append(json.dumps(tool.inputSchema, indent=2))
                    result_lines.append("----------------------------------")
                return "\n".join(result_lines)
    
    async def test_call_tool(self):
        """Test calling a specific tool with hardcoded arguments for demonstration purposes."""

        tool_name = "API-get-users"
        arguments ={
                "properties": {}
            } 
        await self.call_tool(tool_name, arguments)

    async def call_tool(self, tool_name: str, arguments: dict):
        import json
        async with stdio_client(self.server_params) as (read, write): # server is hardcoded to notion for now. TODO - make this configurable in the future.
            async with ClientSession(read, write) as session:
                await session.initialize() 

                result = await session.call_tool(tool_name, arguments)
                
                print("-----------------------------------")
                result_text = result.content[0].text if result.content else "No content returned from tool call."
                print(f"Result from tool call '{tool_name}'\n: {result_text}")
                print("-----------------------------------")

def main():
    """Entry point for the client script."""
    service = MCPService()
    result = asyncio.run(service.list_tools())
    if result:
        print(result)

if __name__ == "__main__":
    main()