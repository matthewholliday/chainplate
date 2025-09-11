from .helpers.template_helper import TemplateHelper
import os
from .services.ux.cli_ux_service import CLIService

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
        self.mcp_services = {}

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
        self.vars["__payload__"] = value
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


    def log_message(self, text: str):
        timestamp = self.get_formatted_timestamp()
        formatted_text = f"[{timestamp}]"
        formatted_text += "\n" + text
        formatted_text += "\n===============END LOG ENTRY================\n"
        self.log(formatted_text)
        return self
    
    def set_payload(self, payload: str):
        self.vars["__payload__"] = payload
        return self
    
    def get_payload(self) -> str:
        return self.get_var(PAYLOAD_KEY)
    
    def set_chat_history(self, chat_history: list) -> None:
        self.conversation_history = chat_history

    def get_chat_history(self) -> list:
        return self.conversation_history  

    def read_chat_history(self) -> str:
        history_text = ""
        for message in self.conversation_history:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            history_text += f"{role.capitalize()}: {content}\n"
        return history_text.strip()  
    
    def get_pipeline_input(self) -> str:
        return self.get_var("__pipeline_input__")
    
    def get_pipeline_output(self) -> str:
        return self.get_var("__pipeline_output__")
    
    def add_mcp_service(self, service_name: str, mcp_service):
        self.mcp_services[service_name] = mcp_service
        return self
    
    def add_mcp_services(self, services: dict):
        if self.mcp_services:
            raise ValueError("Only one mcp service collection can be active at a time. Make sure you don't have nested <load-mcp-tools/> elements in your workflow.")

        for service_name, mcp_service in services.items():
            self.add_mcp_service(service_name, mcp_service)
        return self
    
    def clear_mcp_services(self):
        self.mcp_services = {}
        return self
    
    def print_mcp_services(self):
        for service_name, mcp_service in self.mcp_services.items():
            print(f"MCP Service: {service_name}")
            for tool_name, tool_data in mcp_service.tools.items():
                print(f"  Tool Name: {tool_name}")
                print(f"    Description: {tool_data['description']}")
                print(f"    Input Schema: {tool_data['inputSchema']}")
                print(f"    Output Schema: {tool_data['outputSchema']}")
                print(f"    Annotations: {tool_data['annotations']}")

    def get_mcp_services(self) -> dict:
        return self.mcp_services

    def is_debug_mode(self) -> bool:
        return False
    

