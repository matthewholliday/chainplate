import os
import json

class MCPConfigService:
    def read_mcp_servers_config(file_path: str) -> dict:
        """
        Reads an MCP servers config file (JSON only) and returns its contents.

        Args:
            file_path (str): Path to the MCP servers config file.

        Returns:
            dict: Dictionary of servers under 'mcpServers'.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If parsing fails or 'mcpServers' is missing.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            if "mcpServers" not in config:
                raise ValueError("Invalid config: missing 'mcpServers' section")

            return config["mcpServers"]

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}")
        
    def get_services_list(filepath: str = "mcp/config.json") -> list:
        mcp_servers = MCPConfigService.read_mcp_servers_config(filepath)
        if not mcp_servers:
            raise ValueError("No MCP servers found in config file.")
        return list(mcp_servers.keys())

