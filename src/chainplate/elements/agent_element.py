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
        self.plan_text = "No plan has been created yet."

        #initialize default texts for conversation history, working memory, and planner to ensure they have initial values
        self.conversation_history_text = "The conversation history is currently empty."
        self.working_memory_text = "No working memory has been recorded so far."
        self.planner_text = "No plan has been created yet."

    def enter(self, message: Message) -> Message:
        self.mcp_services = message.mcp_services
        self.tools_overview_text = self.get_master_tool_overview_text(message)
        self.goals_text = message.get_var(self.goals_var_name) or "none"
        self.plan_text = self.generate_plan(message)
        self.next_action_text = self.get_next_action_text(message)
        print("--------------------------------------------------------------------------")
        print(f"Agent '{self.name}' has determined the next action to take based on the current plan and goals.")
        print(f"Next action text: {self.next_action_text}")
        next_action_object = self.convert_action_text_to_object(self.next_action_text)
        self.process_action_object(next_action_object)
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
        goals_are_accomplished = False
        iteration_count = 0
        while not goals_are_accomplished and iteration_count < self.max_iterations:
            message = self.run_agent_iteration(message)
            iteration_count += 1
        
    def run_agent_iteration(self, message: Message) -> Message:
        pass

    # Methods to update and retrieve plan from the message object
    def update_plan(self, message: Message, plan_text: str) -> "AgentElement":
        message.set_var(self.plan_var_name, plan_text)
        return self
    
    def get_current_plan(self, message: Message) -> str:
        return message.get_var(self.plan_var_name)
    
    # Methods to update and retrieve goals from the message object
    def update_goals(self, message: Message, goals_text: str) -> "AgentElement":
        message.set_var(self.goals_var_name, goals_text)
        return self
    
    def get_current_goals(self, message: Message) -> str:
        return message.get_var(self.goals_var_name)
    
    def generate_plan(self, message: Message) -> str:
        return self.send_llm_request(message=message,prompt="Generate a step-by-step plan to achive the following goals based on the current context and tools available. Remember that you are an intelligent agent who is building a plan for you yourself to follow.")
    
    def send_llm_request(self, message: Message, prompt: str) -> str:
        context_string = self.create_context_string(message)
        full_prompt = f"{context_string}\n\n{prompt}"
        response = self.llm_provider.ask_question(system="You are an intelligent agent tasked with assisting in the completion of goals based on the provided context and instructions.", question=full_prompt)
        return response
    
    def create_context_string(self, message: Message) -> str:
        context_parts = [
            "Consider the following when carrying out your tasks: \n",
            f"Log of what has been done so far: {self.agent_log_text}\n",
            f"Your current goals are: {self.goals_text}\n",
            f"Your current plan (if any) is: {self.plan_text}\n",
            f"Your available tools and their descriptions are as follows: {self.tools_overview_text}\n",
            "Based on the above information, please with your instructions(see below):\n"
        ]
        return "\n".join(context_parts)
    
    def get_master_tool_overview_text(self, message: Message) -> str:
        mcp_services = message.get_mcp_services()
        tools_text = ""
        for mcp_service in mcp_services.values():
            for tool_name, tool_data in mcp_service.tools.items():
                tools_text += f"{tool_name} (description={tool_data['description']}) (inputSchema={json.dumps(tool_data['inputSchema'], indent=2)})\n"
        return tools_text.strip()
    
    def convert_action_text_to_object(self, action_text: str) -> ToolCall:
        return json.loads(action_text)
    
    def process_action_object(self, action_object: dict):
        print("Processing action object: ", action_object)
        action = action_object.get("action", "ERROR_MISSING_ACTION")
        
        print("action from obj: ", action)

        if(action == "mcp_tool_call"):
            service_name = action_object.get("service_name", "ERROR_MISSING_SERVICE_NAME")
            tool_name = action_object.get("tool_name", "ERROR_MISSING_TOOL_NAME")
            arguments = action_object.get("arguments", {})
            self.handle_mcp_tool_call(service_name, tool_name, arguments)
        elif(action == "ask_question_to_user"):
            question = action_object.get("question", "ERROR_MISSING_QUESTION")
            self.handle_get_user_input(question)
        elif(action == "modify_plan"):
            new_plan = action_object.get("new_plan", "ERROR_MISSING_NEW_PLAN")
            self.handle_modify_plan(new_plan)

    def handle_mcp_tool_call(self, service_name: str, tool_name: str, arguments: dict) -> str:
        print("HANDLING-MCP-TOOL-CALL")
        print(f"Agent is calling MCP tool '{tool_name}' from service '{service_name}' with arguments: {arguments}...")
        result = self.mcp_services[service_name].call_tool(tool_name, arguments)
        print(f"Result from MCP tool call: {result}")
        print("to be implemented...")

    def handle_get_user_input(self, question: str) -> str:
        print("HANDLING-GET-USER-INPUT")
        user_input = input(f"Agent asked a question: {question}\nPlease provide your answer: ")
        self.append_to_agent_log(f"Agent asked question '{question}' and received user answer: {user_input}")
        return user_input
    
    def handle_modify_plan(self, new_plan: str) -> "AgentElement":
        print("HANDLING-MODIFY-PLAN")
        self.plan_text = new_plan
        self.append_to_agent_log(f"The agent modified the plan based on new information or insights.")
        self.override_plan(new_plan)
        return self

    def override_plan(self, new_plan: str) -> "AgentElement":
        self.plan_text = new_plan
        self.append_to_agent_log(f"The agent's plan was overridden with a new plan.")
        return self

    def append_to_agent_log(self, log_entry: str) -> "AgentElement":
        self.agent_log_text += f"\n{log_entry}"
        return self


    def get_next_action_text(self, message: Message) -> str:
        prompt = ACTION_PLAN_SELCTION_PROMPT
        system_prompt = ACTION_PLAN_SELCTION_SYSTEM
        context_string = self.create_context_string(message)
        full_prompt = f"{system_prompt}\n\n{context_string}\n\n{prompt}"
        response = self.llm_provider.ask_question(system=system_prompt, question=full_prompt)
        return response
    


    
