from .agent_data_service import AgentDataService
from ...message import Message

TOOLS_FILE_NAME = "mcp_tools.json"
WORKING_MEMORY_FILE_NAME = "working_memory.txt"
PLAN_FILE_NAME = "plan.txt"
GOALS_FILE_NAME = "goals.txt"
CONTEXT_FILE_NAME = "context.txt"

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