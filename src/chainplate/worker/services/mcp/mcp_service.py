import json
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio

class MCPService:

    def __init__(self, command, args, env):
        self.server_params = MCPService.get_stdio_params(command, args, env)
        self.tools = {}

    def initialize(self):
        asyncio.run(self.set_tools())
        return self

    def call_tool(self, tool_name: str, arguments: dict = dict()):
        tool_result =  asyncio.run(MCPService.call_stdio_tool(self.server_params, tool_name, arguments))
        return tool_result
    
    def list_tools(self):
        return MCPService.get_stdio_tools(self.server_params)
    
    def set_tool(self,tool: any):
        self.tools[tool.name] = {
            "description": tool.description,
            "inputSchema": tool.inputSchema,
            "outputSchema": tool.outputSchema,
            "annotations": tool.annotations
        }

    async def set_tools(self):
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                for tool in tools.tools:
                    self.set_tool(tool)

    @staticmethod
    def get_stdio_params(command, args, env):
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env)
        return server_params

    @staticmethod
    async def get_stdio_tools(server_params: StdioServerParameters):
        async with stdio_client(server_params) as (read, write):
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
            
    @staticmethod
    async def call_stdio_tool(server_params: StdioServerParameters, tool_name: str, arguments: dict = dict()):
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize() 
                result = await session.call_tool(tool_name, arguments)
                result_text = result.content[0].text if result.content else "{ 'message' : 'No content returned from tool call'}"
                return result_text.strip()