from ..services.data.data_service import DataService
from ..message import Message
from typing import Iterable, Dict, Any, Optional


class AgentData:
    """Access and persist agent-related contextual data.

    After refactor: instance methods no longer accept execution_id; they rely on
    the instance's self.execution_id value provided at construction (or later via setter).
    """

    def __init__(self, execution_id: Optional[int] = None):
        self.data_service = DataService()
        self.execution_id = execution_id

    def set_execution_id(self, execution_id: int) -> None:
        """Update the execution id for subsequent data lookups."""
        self.execution_id = execution_id

    # -------------------------- static helpers -------------------------- #
    @staticmethod
    def concatenate_content(records: Iterable[Dict[str, Any]]) -> str:
        texts = [record["content"] for record in records if record.get("content")]
        return "\n".join(texts)

    # -------------------------- retrieval methods ----------------------- #
    def get_working_memory(self) -> str:
        entries = self.data_service.get_agent_memory(self.execution_id)
        return AgentData.concatenate_content(entries)

    def get_goals(self) -> str:
        entries = self.data_service.get_agent_goal(self.execution_id)
        return AgentData.concatenate_content(entries)

    def get_plan(self) -> str:
        entries = self.data_service.get_agent_plan(self.execution_id)
        return AgentData.concatenate_content(entries)

    def get_services(self, message: Message) -> str:
        service_names = list(message.mcp_services.keys())
        return ", ".join(service_names)

    def get_tools(self, message: Message) -> str:
        tool_descriptions = []
        for service in message.mcp_services.values():
            for tool in service.get_tools():
                tool_descriptions.append(f"{tool['name']}: {tool['description']}")
        return "\n".join(tool_descriptions)

    def get_chat_history_summary(self, message: Message) -> str:
        chat_messages = message.get_chat_history()
        return AgentData.concatenate_content(chat_messages)

    # -------------------------- persistence helpers --------------------- #
    @staticmethod
    def save_goals(data_service: DataService, execution_id: Optional[int] = None, goals: str = "") -> None:
        data_service.upsert_agent_goal_content(execution_id, goals)

    @staticmethod
    def save_plan(data_service: DataService, execution_id: Optional[int] = None, plan: str = "") -> None:
        data_service.upsert_agent_plan_content(execution_id, plan)