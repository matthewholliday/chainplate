from ..services.data.data_service import DataService
from ..message import Message

class AgentData:
    def __init__(self):
        self.data_service = DataService()

    @staticmethod
    def concatenate_content(records) -> str:
        texts = [record["content"] for record in records if record["content"]]
        return "\n".join(texts)

    def get_working_memory(self,execution_id: int=None) -> str:
        entries = self.data_service.get_agent_memory(execution_id)
        return AgentData.concatenate_content(entries)

    def get_goals(self,execution_id: int=None) -> str:
        entries = self.data_service.get_agent_goal(execution_id)
        return AgentData.concatenate_content(entries)

    def get_plan(self,execution_id: int=None) -> str:
        entries = self.data_service.get_agent_plan(execution_id)
        return AgentData.concatenate_content(entries)

    def get_services(self,message: Message) -> str:
        service_names = list(message.mcp_services.keys())
        return ", ".join(service_names)