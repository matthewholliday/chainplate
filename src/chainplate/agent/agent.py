from ..services.mcp.mcp_service import MCPService
from ..services.mcp.mcp_config_service import MCPConfigService
import json

class Agent:
    def __init__(self):
        self.mcp_services = {}
        self.conversation_history_text = "The conversation history is currently empty."
        self.working_memory_text = "No working memory has been recorded so far."
        self.planner_text = "No plan has been created yet."

    def set_conversation_history(self, history_text: str) -> "Agent":
        self.conversation_history_text = history_text
        return self
    
    def set_working_memory(self, memory_text: str) -> "Agent":
        self.working_memory_text = memory_text
        return self
    
    def set_planner_text(self, planner_text: str) -> "Agent":
        self.planner_text = planner_text
        return self

    def create_mcp_service(self, service_name: str, command: str, args: list, env: dict):
        mcp_service = MCPService(command, args, env)
        mcp_service.initialize()
        self.mcp_services[service_name] = mcp_service
        return mcp_service
    
    def load_mcp_service(self, service_name, server_config):
        command = server_config.get("command")
        args = server_config.get("args", [])
        env = server_config.get("env", {})
        self.mcp_services[service_name] = self.create_mcp_service(service_name, command, args, env).initialize()
    
    def load_mcp_services(self, config_file_path: str = "mcp/config.json"):
        mcp_servers_dict = MCPConfigService.read_mcp_servers_config(config_file_path)
        for service_name, server_config in mcp_servers_dict.items():
            self.load_mcp_service(service_name, server_config)

    def get_running_services(self):
        return list(self.mcp_services.keys())
    
    def get_tools_and_descriptions(self, mcp_service: MCPService):
        tools_info = []
        for tool_name, tool_data in mcp_service.tools.items():
            tools_info.append(f"{tool_name} ({tool_data['description']})")
        return tools_info

    def get_master_tool_overview(self):
        overview = []
        for mcp_service in self.mcp_services.values():
            overview.append(self.get_tools_and_descriptions(mcp_service))
        return overview
    
    def get_master_tool_overview_text(self):
        overview = self.get_master_tool_overview()
        overview_text = []
        for service_tools in overview:
            for tool_info in service_tools:
                overview_text.append(tool_info)
        return "\n".join(overview_text)
    
    def get_details_for_tool_text(self, service_name: str, tool_name: str):
        if service_name not in self.mcp_services:
            return f"Service '{service_name}' not found."
        mcp_service = self.mcp_services[service_name]
        if tool_name not in mcp_service.tools:
            return f"Tool '{tool_name}' not found in service '{service_name}'."
        tool_data = mcp_service.tools[tool_name]
        details = [
            f"Tool Name: {tool_name}",
            f"Description: {tool_data['description']}",
            "Input Schema:",
            json.dumps(tool_data['inputSchema'], indent=2),
            "Output Schema:",
            json.dumps(tool_data['outputSchema'], indent=2),
            "Annotations:",
            json.dumps(tool_data['annotations'], indent=2)
        ]
        return "\n".join(details)
    
    def generate_plan(self) -> str:
        context = self.build_context_text()
        from .actions.generate_plan import GeneratePlanAction
        return  GeneratePlanAction().execute(context)
    

    def build_context_text(self) -> str:
        context_parts = [
            "Conversation History: \n",
            self.conversation_history_text,
            "\nWorking Memory: \n",
            self.working_memory_text,
            "\nPlanner Information:\n",
            self.planner_text,
            "\nMCP Services and Tools Overview:\n",
            self.get_master_tool_overview_text()
        ]
        return "\n\n".join(context_parts)
    
    def log_tools(self,tools_text: str) -> None:
        with open("agent/tools.txt", "w") as log_file:
            log_file.write("\n\nTOOLS OVERVIEW:\n")
            log_file.write(tools_text)
            log_file.write("\n\n===================== Agent Memory End ====================\n")

            

