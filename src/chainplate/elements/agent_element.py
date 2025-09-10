from .base_element import BaseElement
from ..message import Message
from ..services.external.prompt_completion_services.openai_llm_provider import OpenAIPromptService
from .constants.agent_prompts import ACTION_PLAN_SELCTION_PROMPT, ACTION_PLAN_SELCTION_SYSTEM
from ..services.mcp.mcp_service import MCPService
import json
from ..services.cli_animation_service import run_with_spinner

class ToolCall:
    def initialize(self, tool_call_str: str):
        try:
            tool_call_json = json.loads(tool_call_str)
            self.service_name = tool_call_json["service_name"]
            self.tool_name = tool_call_json["tool_name"]
            self.arguments = tool_call_json["arguments"]
            self.is_valid = True
        except json.JSONDecodeError:
            self.tool_call_json = None
            self.is_valid = False

    def is_valid(self):
        return self.is_valid

    def get_service_name(self):
        return self.service_name
    
    def get_tool_name(self):
        return self.tool_name
    
    def get_arguments(self):
        return self.arguments


class AgentElement(BaseElement):
    def __init__(self, name="Unnamed Agent", goals="default_goal_var", max_iterations=1):
        super().__init__()

        self.next_action_text = "No action has been determined yet."

        self.llm_provider = OpenAIPromptService()

        #set the name of the agent for identification purposes
        self.name = name

        self.goals_var_name = goals

        #set the maximum number of iterations for the agent to perform its tasks
        self.max_iterations = max_iterations
        self.agent_log_text = "The agent log is currently empty."

        #initialize default texts for conversation history, working memory, and planner to ensure they have initial values
        self.conversation_history_text = "The conversation history is currently empty."
        self.working_memory_text = "No working memory has been recorded so far."

    def enter(self, message: Message) -> Message:
        self.mcp_services = message.mcp_services
        self.tools_overview_text = self.get_master_tool_overview_text(message)
        self.log_tools("tools overview: " + self.tools_overview_text)
        self.goals_text = message.get_var(self.goals_var_name) or "none"
        self.run_agent(message)
        return message

    def exit(self, message) -> Message:
        print("--------------------------------------------------------------------------")
        return message
    
    @staticmethod
    def get_tag() -> str:
        return "agent"
    
    def get_label(self) -> str:
        name_str = f"name={self.name}\n\n"
        goals_str = f"goals={self.goals_var_name}\n\n"
        max_iter_str = f"max_iterations={self.max_iterations}\n\n"
        return [f"AgentElement(\n",name_str, goals_str, max_iter_str, ")\n"]
    
    def run_agent(self, message: Message) -> Message:
        # clear the memory file
        log_file = open("agent/memory.log", "w", encoding="utf-8")
        log_file.write(f"\nNo memories have been recorded so far.\n")
        log_file.close()
        
        # clear the plan file
        plan_file = open("agent/plan.txt", "w", encoding="utf-8")
        plan_file.write(f"\nNo plan has been recorded so far.\n")
        plan_file.close()

        goals_are_accomplished = False
        iteration_count = 0

        self.generate_plan(message=message)

        while not goals_are_accomplished and iteration_count < self.max_iterations:
            goals_are_accomplished = self.run_agent_iteration(message=message)
            iteration_count += 1
            if goals_are_accomplished:
                print(f"[AGENT] The goals have been accomplished after {iteration_count} iterations.")
        
        if not goals_are_accomplished:
            print(f"[AGENT] The agent reached the maximum number of iterations ({self.max_iterations}) without accomplishing the goals.")
        
    def run_agent_iteration(self, message: Message) -> Message:
        print("[AGENT] Thinking...")
        self.next_action_text = self.get_next_action_text(message)
        next_action_object = self.convert_action_text_to_object(self.next_action_text)
        return self.process_action_object(next_action_object)
    
    def generate_plan(self, message: Message) -> str:
        print("[AGENT] Generating a new plan...")
        plan = self.send_llm_request(message=message,prompt="Generate a step-by-step plan to achive the following goals based on the current context and tools available. Remember that you are an intelligent agent who is building a plan for you yourself to follow.")
        self.overwrite_plan_file(plan)
    
    def send_llm_request(self, prompt: str, message: Message) -> str:
        context_string = self.create_context_string(message)
        full_prompt = f"{context_string}\n\n{prompt}"
        response = self.llm_provider.ask_question(system="You are an intelligent agent tasked with assisting in the completion of goals based on the provided context and instructions.", question=full_prompt)
        return response
    
    def create_context_string(self, message: Message) -> str:
        context_parts = [
            "Consider the following when carrying out your tasks: \n",
            f"Log of what has been done so far: {self.get_agent_memory_from_file()}\n",
            f"Your current goals are: {self.goals_text}\n",
            f"Your current plan (if any) is: {self.get_agent_plan_from_file()}\n",
            f"Your current service names are: {self.get_services_overview()}\n",
            f"Your available tools and their descriptions are as follows: {self.get_master_tool_overview_text(message)}\n",
            "Based on the above information, please with your instructions(see below):\n"
        ]
        return "\n".join(context_parts)
    
    def get_agent_memory_from_file(self) -> str:
        memory_file = open("agent/memory.log", "r", encoding="utf-8")
        memory_text = memory_file.read()
        memory_file.close()
        return memory_text.strip()
    
    def get_agent_plan_from_file(self) -> str:
        plan_file = open("agent/plan.txt", "r", encoding="utf-8")
        plan_text = plan_file.read()
        plan_file.close()
        return plan_text.strip()
    
    def get_master_tool_overview_text(self, message: Message) -> str:
        mcp_services = message.get_mcp_services()
        tools_text = ""
        for mcp_service in mcp_services.values():
            for tool_name, tool_data in mcp_service.tools.items():
                tools_text += f"{tool_name} (inputSchema={json.dumps(tool_data['inputSchema'], indent=2)})\n"
        return tools_text.strip()
    
    def convert_action_text_to_object(self, action_text: str) -> ToolCall:
        return json.loads(action_text)
    
    def process_action_object(self, action_object: dict):
        action = action_object.get("action", "ERROR_MISSING_ACTION")
        chain_of_thought = action_object.get("chain_of_thought", "ERROR_MISSING_CHAIN_OF_THOUGHT")
        description = action_object.get("description", "ERROR_MISSING_DESCRIPTION")
        task_is_complete = False

        if(action == "mcp_tool_call"):
            service_name = action_object.get("service_name", "ERROR_MISSING_SERVICE_NAME")
            tool_name = action_object.get("tool_name", "ERROR_MISSING_TOOL_NAME")
            arguments = action_object.get("arguments", {})
            self.handle_mcp_tool_call(service_name, tool_name, arguments, chain_of_thought, description)
        elif(action == "ask_question_to_user"):
            question = action_object.get("question", "ERROR_MISSING_QUESTION")
            self.handle_get_user_input(question, chain_of_thought, description)
        elif(action == "modify_plan"):
            new_plan = action_object.get("new_plan", "ERROR_MISSING_NEW_PLAN")
            self.handle_modify_plan(new_plan, chain_of_thought, description)
        elif(action == "complete_task"):
            result = action_object.get("result", "ERROR_MISSING_RESULT")
            self.handle_complete_task(chain_of_thought, description, result)
            task_is_complete = True
        return task_is_complete

    def handle_mcp_tool_call(self, service_name: str, tool_name: str, arguments: dict, chain_of_thought: str, description: str) -> str:
        print(f"[AGENT] I'm calling MCP tool '{tool_name}' from service '{service_name}'.")
        lowercase_service_name = service_name.lower()
        result = self.mcp_services[lowercase_service_name].call_tool(tool_name, arguments)
        self.remember(f"\n\nDESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nAgent called MCP tool:\n\n  TOOL: '{tool_name}'\n\n  SERVICE: '{service_name}'\n\n  ARGUMENTS: {arguments}\n\n  RESPONSE: \n{result}")
        print(f"[AGENT] I received a result and wrote it to my log.")

    def handle_get_user_input(self, question: str, chain_of_thought: str, description: str) -> str:
        user_input = input(f"[AGENT] I have a question: {question}\n[USER] ")
        self.remember(f"\n\nDESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nI asked question to the user '{question}' and received user answer: {user_input}.")
        print(f"[AGENT] Thanks! I received your answer and added it to my memory.")
        return user_input
    
    def handle_modify_plan(self, new_plan: str, chain_of_thought: str, description: str) -> "AgentElement":
        print("[AGENT] I am modifying my plan based on new information received.")
        self.overwrite_plan_file(new_plan)
        self.remember(f"DESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nI modified the plan based on new information. The new plan is as follows:\n{new_plan}.")
        print(f"[AGENT] The plan is now up-to-date.")
        return self
    
    def handle_complete_task(self, chain_of_thought: str, description: str, result: str) -> "AgentElement":
        print("[AGENT] I have determined that the task has been completed successfully!")
        print("[AGENT] Here is the result: " + result)
        self.remember(f"\n\nDESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nI have completed the task successfully.")
        print(f"[AGENT] The task completion has been logged in my memory.")
        return self

    def remember(self, log_entry: str) -> "AgentElement":
        self.agent_log_text += f"\n{log_entry}"
        log_file = open("agent/memory.log", "a", encoding="utf-8")
        log_file.write(f"{log_entry}\n")
        log_file.close()
        return self

    def get_next_action_text(self, message: Message) -> str:
        prompt = ACTION_PLAN_SELCTION_PROMPT
        system_prompt = ACTION_PLAN_SELCTION_SYSTEM
        context_string = self.create_context_string(message)
        self.log_context(message)
        full_prompt = f"{system_prompt}\n\n{context_string}\n\n{prompt}"
        response = self.llm_provider.ask_question(system=system_prompt, question=full_prompt)
        return response
    
    def overwrite_plan_file(self, new_plan_text: str) -> "AgentElement":
        plan_file = open("agent/plan.txt", "w", encoding="utf-8")
        plan_file.write(f"{new_plan_text}\n")
        plan_file.close()
        return self
    
    def log_tools(self, tools_text: str) -> None:
        log_file = open("agent/tools.log", "w", encoding="utf-8")
        log_file.write(f"{tools_text}\n")
        log_file.close()
        return None
    
    def get_services_overview(self) -> str:
        services_overview = ""
        for service_name in self.mcp_services.keys():
            services_overview += f"\nAvailable Service Name: {service_name}\n"
        return services_overview.strip()

    def log_context(self, message: Message) -> None:
        context_string = self.create_context_string(message)
        log_file = open("agent/context.log", "w", encoding="utf-8")
        log_file.write(f"===================== Agent Context Overview ====================\n")
        log_file.write(f"{context_string}\n")
        log_file.close()
        return None

    
