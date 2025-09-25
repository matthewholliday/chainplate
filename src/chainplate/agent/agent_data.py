from ..services.data.data_service import DataService
from ..message import Message
from typing import Iterable, Dict, Any, Optional
from ..services.logging.logging_service import LoggingService


class AgentData:
    """Access and persist agent-related contextual data.

    After refactor: instance methods no longer accept execution_id; they rely on
    the instance's self.execution_id value provided at construction (or later via setter).
    """

    def __init__(self, execution_id: int):
        self.data_service = DataService()
        self.execution_id = execution_id
        LoggingService.log_info(f"AgentData initialized with execution_id: {self.execution_id}")
    
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
            for tool in service.list_tools():
                tool_descriptions.append(tool)
        return "".join(tool_descriptions)

    def get_chat_history_summary(self, message: Message) -> str:
        chat_messages = self.data_service.get_execution_steps(self.execution_id)
        chat_message_strings = []
        for msg in chat_messages:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            chat_message_strings.append(f"{role}: {content}")
        return AgentData.concatenate_content(chat_messages)

    # -------------------------- persistence helpers --------------------- #
    def save_goals(self, goals: str = "") -> None:
        self.data_service.upsert_agent_goal_content(self.execution_id, goals)

    def save_plan(self, plan: str = "") -> None:
        self.data_service.upsert_agent_plan_content(self.execution_id, plan)

    def add_memory(self, entry: str = "") -> None:
        self.data_service.add_agent_memory(self.execution_id, entry)