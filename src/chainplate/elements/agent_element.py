import json
from ..message import Message
from ..services.cli_service import CLIService as CliIService
from ..services.external.prompt_completion_services.openai_llm_provider import OpenAIPromptService
from .base_element import BaseElement
from .constants.agent_prompts import ACTION_PLAN_SELCTION_PROMPT, ACTION_PLAN_SELCTION_SYSTEM
from ..services.data.file_system_data_service import FileSystemDataService

class AgentElement(BaseElement):
    def __init__(self, name="Unnamed Agent", goals="default_goal_var", output_var="__payload__", max_iterations=1, ux_service=CliIService(), data_service=FileSystemDataService(base_path="data/agent")):
        super().__init__()

        self.next_action_text = "No action has been determined yet."

        self.llm_provider = OpenAIPromptService()

        #set the name of the agent for identification purposes
        self.name = name

        self.goals_var_name = goals

        self.payload_var_name = output_var

        #set the maximum number of iterations for the agent to perform its tasks
        self.max_iterations = max_iterations

        #initialize default texts for conversation history, working memory, and planner to ensure they have initial values
        self.conversation_history_text = "The conversation history is currently empty."

        self.ux_service = ux_service

        self.data_service = data_service

        self.inherited_context = ""

    def enter(self, message: Message) -> Message:
        self.inherited_context = message.read_context()
        self.data_service.clear_data()
        self.data_service.save_chat_history_summary(message)

        self.mcp_services = message.mcp_services

        goals_value = message.get_var(self.goals_var_name)
        self.data_service.save_goals(content=goals_value)
        message = self.run_agent(message)
        return message

    def exit(self, message) -> Message:
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

        self.generate_plan(message=message)

        while not goals_are_accomplished and iteration_count < self.max_iterations:
            goals_are_accomplished, message = self.run_agent_iteration(message=message)
            iteration_count += 1
            if goals_are_accomplished:
                self.print_agent_output(f"iteration count: {iteration_count}")
        
        if not goals_are_accomplished:
            self.print_agent_output(f"I reached the maximum number of iterations ({self.max_iterations}) without accomplishing the goals.")
        
        return message
        
    def run_agent_iteration(self, message: Message) -> tuple[bool, Message]:
        self.print_agent_output("Thinking about my next action...")
        self.next_action_text = self.get_next_action_text(message)
        next_action_object = self.convert_action_text_to_object(self.next_action_text)
        is_complete, message = self.process_action_object(next_action_object, message)
        return (is_complete, message)
    
    def generate_plan(self, message: Message) -> str:
        self.print_agent_output(f"Generating a new plan...")
        plan = self.send_llm_request(message=message,prompt="Generate a step-by-step plan to achive the following goals based on the current context and tools available. Remember that you are an intelligent agent who is building a plan for you yourself to follow.")
        self.data_service.save_plan(plan)
    
    def send_llm_request(self, prompt: str, message: Message) -> str:
        context_string = self.create_context_string(message)
        full_prompt = f"{context_string}\n\n{prompt}"
        response = self.llm_provider.ask_question(system="You are an intelligent agent tasked with assisting in the completion of goals based on the provided context and instructions.", question=full_prompt)
        return response
    
    def create_context_string(self, message: Message) -> str:
        working_memory = self.data_service.get_working_memory()
        current_goals = self.data_service.get_goals()
        current_plan = self.data_service.get_plan()
        services = self.data_service.get_services(message)
        tools = self.data_service.get_tools(message)
        
        if(message.is_debug_mode()):
            if(not self.inherited_context):
                self.print_agent_output(f"Note: There is no inherited context from previous elements.")

            if(not working_memory):
                self.print_agent_output(f"Note: The working memory is currently empty.")

            if(not current_goals):
                self.print_agent_output(f"Note: The current goals empty.")

            if(not current_plan):
                self.print_agent_output(f"Note: The current plan is empty.")
            
            if(not services):
                self.print_agent_output(f"Note: There are no services available.")

            if(not tools):
                self.print_agent_output(f"Note: There are no tools available.")

        context_parts = [
            "Consider the following when carrying out your tasks: \n",
            f"Log of what has been done so far: {self.data_service.get_working_memory()}\n",
            f" >>> Chat history summary: {self.data_service.get_chat_history_summary(message)}\n",
            f" >>> The inherited context from previous stages of the process is as follows: {self.inherited_context}\n",
            # f" >>> Your current goals are: {self.data_service.get_goals()}\n",
            f" >>> Your current plan (if any) is: {self.data_service.get_plan()}\n",
            f" >>> Your current service names are: {self.data_service.get_services(message)}\n",
            f" >>> Your available tools and their descriptions are as follows: {self.data_service.get_tools(message)}\n",
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
    
    def convert_action_text_to_object(self, action_text: str):
        return json.loads(action_text)
    
    def process_action_object(self, action_object: dict, message: Message) -> tuple[bool, Message]:
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
            message = self.handle_complete_task(chain_of_thought, description, result, message)
            task_is_complete = True
        return (task_is_complete, message)

    def handle_mcp_tool_call(self, service_name: str, tool_name: str, arguments: dict, chain_of_thought: str, description: str):
        self.print_agent_output(f"I'm calling MCP tool '{tool_name}' from service '{service_name}'.")
        lowercase_service_name = service_name.lower()
        result = self.mcp_services[lowercase_service_name].call_tool(tool_name, arguments)
        self.data_service.append_working_memory(f"\n\nDESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nAgent called MCP tool:\n\n  TOOL: '{tool_name}'\n\n  SERVICE: '{service_name}'\n\n  ARGUMENTS: {arguments}\n\n  RESPONSE: \n{result}")
        self.print_agent_output(f"I received a result and wrote it to my log.")

    def handle_get_user_input(self, question: str, chain_of_thought: str, description: str):
        self.print_agent_output("I have a question:")
        user_input = self.get_user_input(question)
        self.data_service.append_working_memory(f"\n\nDESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nI asked question to the user '{question}' and received user answer: {user_input}.")
        self.print_agent_output("Thanks! I received your answer and added it to my memory.")
        return user_input
    
    def handle_modify_plan(self, new_plan: str, chain_of_thought: str, description: str):
        self.print_agent_output("I am modifying my plan based on new information received.")
        self.data_service.save_plan(new_plan)
        self.data_service.append_working_memory(f"DESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nI modified the plan based on new information. The new plan is as follows:\n{new_plan}.")
        self.print_agent_output("The plan is now up-to-date.")
    
    def handle_complete_task(self, chain_of_thought: str, description: str, result: str, message: Message) -> Message:
        self.print_agent_output("I have determined that the task has been completed successfully!")
        self.print_agent_output("Here is the result: " + result)
        self.data_service.append_working_memory(f"\n\nDESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nI have completed the task successfully.")
        self.print_agent_output("The task completion has been logged in my memory.")
        message.set_var(self.payload_var_name, result)
        return message

    def get_next_action_text(self, message: Message) -> str:
        response = self.send_llm_request(prompt=ACTION_PLAN_SELCTION_PROMPT, message=message)
        return response

    def print_agent_output(self, text: str) -> None:
        self.ux_service.show_output_to_user(f"[AGENT] {text}")

    def get_user_input(self, prompt: str) -> str:
        return self.ux_service.get_input_from_user(f"[USER] {prompt}")
    
