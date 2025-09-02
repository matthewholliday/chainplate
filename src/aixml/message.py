from .helpers.template_helper import TemplateHelper
from .helpers.prompt_helper import ask as prompt_ask
from .helpers.prompt_helper import chat as prompt_chat
import os
from .services.cli_service import CLIService

CONTEXT_KEY = "__context__"
PAYLOAD_KEY = "__payload__"
CHAT_INPUT_KEY = "__chat_input__" # This is the latest message that was sent to the chat. It may or may not be equal to the payload, depending on how the workflow is designed.
CHAT_RESPONSE_KEY = "__chat_response__"

class Message:
    def __init__(self):
        self.logs = []
        self.vars = {}
        self.context_stack = []
        self.vars[CONTEXT_KEY] = self.read_context()
        self.conversation_history = []  # For chat mode

    def update_context_var(self):
        self.vars[CONTEXT_KEY] = self.read_context()
        return self

    def push_context(self, content: str):
        self.context_stack.append(content)
        self.update_context_var()
        return self

    def pop_context(self):
        if self.context_stack:
            return self.context_stack.pop()
        self.update_context_var()
        return self
    
    def read_context(self):
        context = "\n".join(self.context_stack)
        return context

    def log(self, message: str):
        self.logs.append(message)

    def get_logs(self):
        return self.logs
    
    def print_logs(self):
        # print all logs to logs/execution.log (overwrite instead of append)
        os.makedirs("logs", exist_ok=True)
        with open("logs/execution.log", "w", encoding="utf-8") as f:
            for log in self.logs:
                f.write(log + "\n")

    def set_var(self, key: str, value):
        self.vars[key] = value
        return self

    def has_var(self, key: str) -> bool:
        return key in self.vars
    
    def get_var(self, key: str):
        return self.vars.get(key, None)
    
    def get_vars(self):
        return self.vars
    
    def get_formatted_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    def log_message(self, text: str) -> str:
        timestamp = self.get_formatted_timestamp()
        formatted_text = f"[{timestamp}]"
        formatted_text += "\n" + text
        formatted_text += "\n===============END LOG ENTRY================\n"
        self.log(formatted_text)
        return formatted_text
    
    def set_payload(self, payload: str):
        self.set_var(PAYLOAD_KEY, payload)
        return self
    
    def prompt_chat(self) -> list:
        self.conversation_history = prompt_chat(self.conversation_history)
        return self
    
    def get_payload(self) -> str:
        return self.get_var(PAYLOAD_KEY)
    
    def set_chat_history(self, chat_history: list) -> None:
        self.conversation_history = chat_history

    def get_chat_history(self) -> list:
        return self.conversation_history    
    
    def get_chat_input(self):
        return self.get_var(CHAT_INPUT_KEY)
    
    def set_chat_input(self, chat_input: str):
        self.set_var(CHAT_INPUT_KEY, chat_input)
        return self
    
    def get_chat_response(self):
        return self.get_var(CHAT_RESPONSE_KEY)
    
    def set_chat_response(self, chat_response: str):
        self.set_var(CHAT_RESPONSE_KEY, chat_response)
        return self

