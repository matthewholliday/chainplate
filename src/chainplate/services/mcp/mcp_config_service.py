import os
import json

class MCPConfigService:
    def read_mcp_servers_config(file_path: str) -> dict:
        mcp_config_text = """
{
    "mcpServers": {
        "notion": {
            "type" : "stdio",
            "command" : "npx",
            "args" : ["-y", "@notionhq/notion-mcp-server"],
            "env": { "NOTION_TOKEN": "ntn_b89841075978RYBDlJ8XFoUZYblF89YINv7MystOtNW2Uo" },
            "description" : "Notion is a tool for semistructured data storage and retrieval, allowing users to create, manage, and query databases and documents."
        },
        "fetch" : {
            "type" : "stdio",
            "command": "uvx",
            "args": ["mcp-server-fetch"]
        }
    }
}

        """
        config = json.loads(mcp_config_text)

        if "mcpServers" not in config:
            raise ValueError("Invalid config: missing 'mcpServers' section")

        return config["mcpServers"]
        
    def get_services_list(filepath: str = "mcp/config.json") -> list:
        mcp_servers = MCPConfigService.read_mcp_servers_config(filepath)
        if not mcp_servers:
            raise ValueError("No MCP servers found in config file.")
        return list(mcp_servers.keys())

