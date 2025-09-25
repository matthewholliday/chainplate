import json
from ..message import Message
from ..services.external.prompt_completion_services.openai_llm_provider import OpenAIPromptService
from .base_element import BaseElement
from .constants.agent_prompts import ACTION_PLAN_SELECTION_PROMPT, ACTION_PLAN_SELCTION_SYSTEM
from ..agent.agent_data import AgentData
from ..agent.agent_environment import AgentEnvironment
from ..execution_context import ExecutionContext
from ..services.logging.logging_service import LoggingService
import traceback

class AgentElement(BaseElement):
    def __init__(self, name="Unnamed Agent", goals="default_goal_var", output_var="__payload__", max_iterations=1, context: ExecutionContext = None):
        super().__init__(context=context)

        self.next_action_text = "No action has been determined yet."

        self.llm_provider = OpenAIPromptService()

        #set the name of the agent for identification purposes
        self.name = name

        self.goals_var_name = goals
        LoggingService.log_info(f"Agent goals variable name set to: {self.goals_var_name}")

        self.payload_var_name = output_var

        #set the maximum number of iterations for the agent to perform its tasks
        self.max_iterations = max_iterations

        #initialize default texts for conversation history, working memory, and planner to ensure they have initial values
        self.conversation_history_text = "The conversation history is currently empty."

        self.inherited_context = ""

        self.context = context
        self.execution_id = context.execution_id

        LoggingService.log_info(f"Initializing AgentElement with execution_id: {self.execution_id}")
        self.agent_data = AgentData(execution_id=self.execution_id)
        self.agent_environment = AgentEnvironment(execution_id=self.execution_id)


    def enter(self, message: Message) -> Message:
        self.inherited_context = message.read_context()
        self.mcp_services = message.mcp_services

        goals_value = message.get_var(self.goals_var_name)
        if(goals_value):
            self.agent_data.save_goals(goals=goals_value)
            LoggingService.log_info(f"LOADED AGENT GOALS: \n\n  VAR_NAME:\n'{self.goals_var_name}':\n\n  VALUE:\n{goals_value}")
        else:
            LoggingService.log_warning(f"Agent goals variable '{self.goals_var_name}' not found in message. Using empty goals list.")
            self.agent_data.save_goals(goals="")

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
                self.agent_environment.send_to_user(f"iteration count: {iteration_count}")
        
        if not goals_are_accomplished:
            self.agent_environment.send_to_user(f"I reached the maximum number of iterations ({self.max_iterations}) without accomplishing the goals.")
        
        return message
        
    def run_agent_iteration(self, message: Message) -> tuple[bool, Message]:
        self.agent_environment.send_to_user("Thinking about my next action...")
        self.next_action_text = self.get_next_action_text(message)
        next_action_object = self.convert_action_text_to_object(self.next_action_text)
        is_complete, message = self.process_action_object(next_action_object, message)
        return (is_complete, message)
    
    def create_generate_plan_prompt(self, message: Message) -> str:
        goals_text = self.agent_data.get_goals()
        prompt = f"Generate a step-by-step plan to archive the following goals based on the current context and tools available. Remember that you are an intelligent agent who is building a plan for you yourself to follow: {goals_text}"
        return prompt

    def generate_plan(self, message: Message) -> str:
        self.agent_environment.send_to_user(f"Generating a new plan...")
        prompt_text = self.create_generate_plan_prompt(message)
        LoggingService.log_info(f"Prompt for generating plan:\n\n{prompt_text}")
        plan = self.send_llm_request(prompt=prompt_text,message=message)
        self.agent_environment.send_to_user(f"Okay! Here's my plan...\n\n{plan}")
        self.agent_data.save_plan(plan=plan)
    
    def send_llm_request(self, prompt: str = "", message: Message = None) -> str:
        context_string = self.create_context_string(message)
        full_prompt = f"{context_string}\n\n{prompt}"
        response = self.llm_provider.ask_question(system="You are an intelligent agent tasked with assisting in the completion of goals based on the provided context and instructions.", question=full_prompt)
        return response
    
    def create_context_string(self, message: Message) -> str:
        working_memory = self.agent_data.get_working_memory()
        current_goals = self.agent_data.get_goals()
        current_plan = self.agent_data.get_plan()
        services = self.agent_data.get_services(message)
        tools = self.agent_data.get_tools(message)
        
        if(message.is_debug_mode()):
            if(not self.inherited_context):
                self.agent_environment.send_to_user(f"Note: There is no inherited context from previous elements.")

            if(not working_memory):
                self.agent_environment.send_to_user(f"Note: The working memory is currently empty.")

            if(not current_goals):
                self.agent_environment.send_to_user(f"Note: The current goals empty.")

            if(not current_plan):
                self.agent_environment.send_to_user(f"Note: The current plan is empty.")
            
            if(not services):
                self.agent_environment.send_to_user(f"Note: There are no services available.")

            if(not tools):
                self.agent_environment.send_to_user(f"Note: There are no tools available.")
                

        context_parts = [
            "Consider the following when carrying out your tasks: \n",
            f"Log of what has been done so far: {self.agent_data.get_working_memory()}\n",
            f" >>> Chat history summary: {self.agent_data.get_chat_history_summary(message)}\n\n",
            f" >>> The inherited context from previous stages of the process is as follows: {self.inherited_context}\n\n",
            f" >>> Your current plan (if any) is: {self.agent_data.get_plan()}\n\n",
            f" >>> Your current service names are: {self.agent_data.get_services(message)}\n\n",
            f" >>> Your available tools and their descriptions are as follows: {self.agent_data.get_tools(message)}]\n\n",
            f" >>> Your current goals are: {self.agent_data.get_goals()}\n\n",
            "Based on the above information, proceed with your instructions."
        ]
        context = "\n".join(context_parts)

        LoggingService.log_info(f"Context for LLM request created:\n\n {context}")

        return context

    
    def convert_action_text_to_object(self, action_text: str):
        action_object = {}
        try:
            action_object = json.loads(action_text)
        except json.JSONDecodeError as e:
            LoggingService.log_error(f"(chainplate) [GET-NEXT-ACTION-ERROR]Error parsing action text to JSON: Here is the action text that caused the error:\n{action_text}\n\nError details: {e}\n{traceback.format_exc()}")
            self.agent_environment.send_to_user("I encountered an error while trying to understand my next action. I'll try again.")
            action_object = {
                "action": "ERROR_PARSING_ACTION",
                "chain_of_thought": "I encountered an error while trying to parse the action text to JSON.",
                "description": "The action text could not be parsed to JSON.",
            }
        return action_object
    
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

    def create_handle_tool_call_memory_string(self, description: str, chain_of_thought: str, tool_name: str, service_name: str, arguments: any, result) -> str:
        memory_string = f"\n\nDESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nAgent called MCP tool:\n\n  TOOL: '{tool_name}'\n\n  SERVICE: '{service_name}'\n\n  ARGUMENTS: {arguments}\n\n  RESPONSE: \n{result}"
        LoggingService.log_info(f"Tool call memory string created:\n {memory_string}")
        return memory_string
    
    def create_handle_user_input_memory_string(self, description: str, chain_of_thought: str, question: str, user_input: str) -> str:
        memory_string = f"\n\nDESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nI asked question to the user '{question}' and received user answer: {user_input}."
        LoggingService.log_info(f"User input memory string created:\n {memory_string}")
        return memory_string
    
    def create_handle_modify_plan_memory_string(self, description: str, chain_of_thought: str, new_plan: str) -> str:
        memory_string = f"DESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nI modified the plan based on new information. The new plan is as follows:\n{new_plan}."
        LoggingService.log_info(f"Modify plan memory string created:\n {memory_string}")
        return memory_string
    
    def create_handle_complete_task_memory_string(self, description: str, chain_of_thought: str) -> str:
        memory_string = f"\n\nDESCRIPTION: {description}\n\nCHAIN OF THOUGHT: {chain_of_thought}\n\nI have completed the task successfully."
        LoggingService.log_info(f"Complete task memory string created:\n {memory_string}")
        return memory_string

    def handle_mcp_tool_call(self, service_name: str, tool_name: str, arguments: dict, chain_of_thought: str, description: str):
        self.agent_environment.send_to_user(f"I'm calling MCP tool '{tool_name}' from service '{service_name}'.")
        lowercase_service_name = service_name.lower()
        result = self.mcp_services[lowercase_service_name].call_tool(tool_name, arguments)
        self.agent_data.add_memory(entry=self.create_handle_tool_call_memory_string(description, chain_of_thought, tool_name, service_name, arguments, result))
        self.agent_environment.send_to_user(f"I received a result and wrote it to my log.")

    def handle_get_user_input(self, question: str, chain_of_thought: str, description: str):
        self.agent_environment.send_to_user("I have a question:")
        user_input = self.get_user_input(question)
        self.agent_data.add_memory(entry=self.create_handle_user_input_memory_string(description, chain_of_thought, question, user_input))
        self.agent_environment.send_to_user("Thanks! I received your answer and added it to my memory.")
        return user_input
    
    def handle_modify_plan(self, new_plan: str, chain_of_thought: str, description: str):
        self.agent_environment.send_to_user("I am modifying my plan based on new information received.")
        self.agent_data.save_plan(new_plan)
        self.agent_data.add_memory(entry=self.create_handle_modify_plan_memory_string(description, chain_of_thought, new_plan))
        self.agent_environment.send_to_user("The plan is now up-to-date.")
    
    def handle_complete_task(self, chain_of_thought: str, description: str, result: str, message: Message) -> Message:
        self.agent_environment.send_to_user("I have determined that the task has been completed successfully!")
        self.agent_environment.send_to_user("Here is the result: " + result)
        self.agent_data.add_memory(entry=self.create_handle_complete_task_memory_string(description, chain_of_thought))
        self.agent_environment.send_to_user("The task completion has been logged in my memory.")
        message.set_var(self.payload_var_name, result)
        return message

    def get_next_action_text(self, message: Message) -> str:
        response = self.send_llm_request(prompt=ACTION_PLAN_SELECTION_PROMPT, message=message)
        LoggingService.log_info(f"(chainplate) [NEXT-ACTION-TEXT (should be JSON-parseable):\n\n{response}")
        return response

    def print_agent_output(self, text: str) -> None:
        self.agent_environment.send_to_user(f"{text}")

    def get_user_input(self, prompt: str) -> str:
        return self.agent_environment.get_user_input(f"{prompt}")
    
