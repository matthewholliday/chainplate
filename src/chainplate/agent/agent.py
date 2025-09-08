from ..services.mcp.mcp_service import MCPService
from ..services.mcp.mcp_config_service import MCPConfigService
import json

class Agent:

    def __init__(self):
        self.mcp_services = {}

    def create_mcp_service(self, service_name: str, command: str, args: list, env: dict):
        mcp_service = MCPService(command, args, env)
        mcp_service.initialize()
        self.mcp_services[service_name] = mcp_service
        return mcp_service
    
    def load_mcp_service(self, service_name, server_config):
        command = server_config.get("command")
        args = server_config.get("args", [])
        env = server_config.get("env", {})
        self.mcp_services[service_name] = self.create_mcp_service(service_name, command, args, env).initialize()
    
    def load_mcp_services(self, config_file_path: str = "mcp/config.json"):
        mcp_servers_dict = MCPConfigService.read_mcp_servers_config(config_file_path)
        for service_name, server_config in mcp_servers_dict.items():
            self.load_mcp_service(service_name, server_config)

    def get_running_services(self):
        return list(self.mcp_services.keys())
    
    def get_tools_and_descriptions(self, mcp_service: MCPService):
        tools_info = []
        for tool_name, tool_data in mcp_service.tools.items():
            tools_info.append(f"{tool_name} ({tool_data['description']})")
        return tools_info

    def get_master_tool_overview(self):
        overview = []
        for mcp_service in self.mcp_services.values():
            overview.append(self.get_tools_and_descriptions(mcp_service))
        return overview
    
    def get_master_tool_overview_text(self):
        overview = self.get_master_tool_overview()
        overview_text = []
        for service_tools in overview:
            for tool_info in service_tools:
                overview_text.append(tool_info)
        return "\n".join(overview_text)


            

