from .agent_data_service import AgentDataService
from ...message import Message

TOOLS_FILE_NAME = "mcp_tools.json"
WORKING_MEMORY_FILE_NAME = "working_memory.txt"
PLAN_FILE_NAME = "plan.txt"
GOALS_FILE_NAME = "goals.txt"
CONTEXT_FILE_NAME = "context.txt"
CHAT_HISTORY_SUMMARY_FILE_NAME = "chat_history_summary.txt"

class FileSystemDataService(AgentDataService):

    def __init__(self, base_path: str):
        self.base_path = base_path

    def clear_data(self):
        # Clear working memory
        working_memory_path = f"{self.base_path}/{WORKING_MEMORY_FILE_NAME}"
        open(working_memory_path, "w", encoding="utf-8").close()

        # Clear plan
        plan_path = f"{self.base_path}/{PLAN_FILE_NAME}"
        open(plan_path, "w", encoding="utf-8").close()

        # Clear goals
        goals_path = f"{self.base_path}/{GOALS_FILE_NAME}"
        open(goals_path, "w", encoding="utf-8").close()

    def append_working_memory(self, content: str):
        working_memory_path = f"{self.base_path}/{WORKING_MEMORY_FILE_NAME}"
        with open(working_memory_path, "a", encoding="utf-8") as f:
            f.write(content + "\n")

    def get_working_memory(self) -> str:
        working_memory_path = f"{self.base_path}/{WORKING_MEMORY_FILE_NAME}"
        try:
            with open(working_memory_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""
        
    def save_plan(self, content: str):
        plan_path = f"{self.base_path}/{PLAN_FILE_NAME}"
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(content)

    def get_plan(self) -> str:
        plan_path = f"{self.base_path}/{PLAN_FILE_NAME}"
        try:
            with open(plan_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""
        
    def save_goals(self, content: str):
        goals_path = f"{self.base_path}/{GOALS_FILE_NAME}"
        with open(goals_path, "w", encoding="utf-8") as f:
            f.write(content)

    def save_context(self, content: str):
        context_path = f"{self.base_path}/{CONTEXT_FILE_NAME}"
        with open(context_path, "w", encoding="utf-8") as f:
            f.write(content)

    def get_goals(self) -> str:
        goals_path = f"{self.base_path}/{GOALS_FILE_NAME}"
        try:
            with open(goals_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""
        
    def get_chat_history_summary(self, message):
        chat_history_path = f"{self.base_path}/{CHAT_HISTORY_SUMMARY_FILE_NAME}"
        try:
            with open(chat_history_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return ""
    
    def save_chat_history_summary(self, message) -> None:
        self.save_chat_history_full(message)
        summary = AgentDataService.generate_chat_history_summary(message)
        chat_history_path = f"{self.base_path}/{CHAT_HISTORY_SUMMARY_FILE_NAME}"
        with open(chat_history_path, "w", encoding="utf-8") as f:
            f.write(summary)

    def save_chat_history_full(self, message: Message) -> None:
        chat_history_path = f"{self.base_path}/chat_history_full.txt"
        full_history = message.read_chat_history()
        with open(chat_history_path, "w", encoding="utf-8") as f:
            f.write(full_history)