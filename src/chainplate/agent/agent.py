from ..services.mcp.mcp_service import MCPService
from ..services.mcp.mcp_config_service import MCPConfigService

class Agent:

    def __init__(self):
        self.mcp_services = {}

    def create_mcp_service(self, service_name: str, command: str, args: list, env: dict):
        mcp_service = MCPService(command, args, env)
        mcp_service.initialize()
        self.mcp_services[service_name] = mcp_service
        return mcp_service
    
    def load_mcp_service(self, server_config):
        service_name = server_config.get("name")
        command = server_config.get("command")
        args = server_config.get("args", [])
        env = server_config.get("env", {})
        self.mcp_services[service_name] = self.create_mcp_service(service_name, command, args, env).initialize()
    
    def load_mcp_services(self, config_file_path: str = "mcp/config.json"):
        for server in MCPConfigService.read_mcp_servers_config(config_file_path):
            self.load_mcp_service(server)

