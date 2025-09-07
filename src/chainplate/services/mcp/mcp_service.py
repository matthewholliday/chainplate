import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class McpService:

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
    async def call_stdio_tool(server_params: StdioServerParameters, tool_name: str, arguments: dict):
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize() 
                result = await session.call_tool(tool_name, arguments)
                result_text = result.content[0].text if result.content else "No content returned from tool call."
                return f"Result from tool call '{tool_name}' was: \n\n {result_text}"