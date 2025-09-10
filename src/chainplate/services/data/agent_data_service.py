from abc import ABC, abstractmethod
from ...message import Message
from ...services.mcp.mcp_service import MCPService
import json

class AgentDataService(ABC):

    @abstractmethod
    def append_working_memory(self, content: str):
        pass

    @abstractmethod
    def get_working_memory(self) -> str:
        pass

    @abstractmethod
    def save_plan(self, content: str):
        pass

    @abstractmethod
    def get_plan(self) -> str:
        pass

    @abstractmethod
    def save_goals(self, content: str):
        pass

    @abstractmethod
    def get_goals(self) -> str:
        pass

    @staticmethod
    def get_tools(message: Message) -> str:
        mcp_services = message.get_mcp_services()
        tools_text = ""
        for mcp_service in mcp_services.values():
            for tool_name, tool_data in mcp_service.tools.items():
                tools_text += f"{tool_name} (inputSchema={json.dumps(tool_data['inputSchema'], indent=2)})\n"
        return tools_text.strip()
    
    @staticmethod
    def get_services(message: Message) -> str:
        mcp_services = message.get_mcp_services()
        services_overview = ""
        for service_name in mcp_services.keys():
            services_overview += f"\nAvailable Service Name: {service_name}\n"
        return services_overview.strip()


    