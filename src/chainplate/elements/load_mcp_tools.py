from .base_element import BaseElement
from ..services.mcp.mcp_service import MCPService
from ..services.mcp.mcp_config_service import MCPConfigService
from ..message import Message

class LoadMCPToolsElement(BaseElement):

    def __init__(self, mcp_services_string: str = ""):
        super().__init__()
        self.mcp_services = self.create_services(self.parse_services(mcp_services_string))

    def parse_services(self, services_string: str = ""):
        return [services_string.strip() for service in services_string.split(",")]

    def create_mcp_service(self, command: str, args: list, env: dict):
        mcp_service = MCPService(command, args, env)
        mcp_service.initialize()
        return mcp_service
    
    def create_services(self, service_names: list[str], config_file_path: str = "mcp/config.json") -> dict[str, MCPService]:
        from ..services.mcp.mcp_config_service import MCPConfigService

        mcp_servers_dict = MCPConfigService.read_mcp_servers_config(config_file_path)
        services = {}
        for service_name in service_names:
            if service_name in mcp_servers_dict:
                server_config = mcp_servers_dict[service_name]
                command = server_config.get("command")
                args = server_config.get("args", [])
                env = server_config.get("env", {})
                services[service_name] = self.create_mcp_service(command, args, env)
        return services
    
    def enter(self, message: Message):
        message.add_mcp_services(self.mcp_services)
        return message
    
    def exit(self, message: Message):
        message.clear_mcp_services()
        return message
