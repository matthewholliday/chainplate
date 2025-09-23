from .base_element import BaseElement
from ..services.mcp.mcp_service import MCPService
from ..services.data.data_service import DataService
from ..message import Message
from ..execution_context import ExecutionContext

class LoadMCPToolsElement(BaseElement):

    def __init__(self, mcp_services_string: str = "", context: ExecutionContext = None):
        super().__init__(context=context)
        services_list = self.parse_services(mcp_services_string)
        self.mcp_services = self.create_services(services_list)
        self.context = context

    def parse_services(self, services_string: str = ""):
        return services_string.split(",") if services_string else []

    def create_mcp_service(self, command: str, args: list, env: dict):
        mcp_service = MCPService(command, args, env)
        mcp_service.initialize()
        return mcp_service
    
    def create_services(self, service_names: list[str]) -> dict[str, MCPService]:
        """
        Build MCPService instances from persisted definitions in DataService.

        DataService.get_mcp_services returns a list of dicts with keys:
          name, type, command, args (list), description, env (list[str])

        env is stored denormalized as list of "KEY=VALUE" strings; convert to
        a dict for MCPService (which expects an env mapping) while skipping
        malformed entries gracefully.
        """
        ds = DataService()
        stored = {svc['name']: svc for svc in ds.get_mcp_services() if svc.get('name')}
        selected = service_names or list(stored.keys())
        services: dict[str, MCPService] = {}
        for name in selected:
            svc = stored.get(name)
            if not svc:
                # silently skip unknown names; could log if logging available
                continue
            command = svc.get('command')
            args = svc.get('args') or []
            raw_env_list = svc.get('env') or []
            env_dict = {}
            if isinstance(raw_env_list, list):
                for item in raw_env_list:
                    if not isinstance(item, str):
                        continue
                    if '=' in item:
                        k, v = item.split('=', 1)
                        k = k.strip()
                        if k:
                            env_dict[k] = v
            services[name] = self.create_mcp_service(command, args, env_dict)
        return services
    
    def enter(self, message: Message):
        message.add_mcp_services(self.mcp_services)
        return message
    
    def exit(self, message: Message):
        message.clear_mcp_services()
        return message

    @staticmethod
    def get_tag() -> str:
        return "load-mcp-services"
    
    def get_label(self) -> str:
        return f"LoadMCPToolsElement(services={list(self.mcp_services.keys())})"