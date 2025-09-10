from abc import ABC, abstractmethod
from ...message import Message
from ...services.mcp.mcp_service import MCPService
import json
from ...services.summarization_service import SummarizationService

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

    @abstractmethod
    def get_chat_history_summary(self, message) -> str:
        pass

    @abstractmethod
    def save_chat_history_summary(self, message) -> None:
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
    
    @staticmethod
    def generate_chat_history_summary(message: Message) -> str:
        full_history = message.read_chat_history()
        summarization_service = SummarizationService()
        summary = summarization_service.summarize(full_history)
        return summary

