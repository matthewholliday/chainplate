import traceback
from ..message import Message
from ..services.external.prompt_completion_services.openai_llm_provider import OpenAIPromptService
from .base_element import BaseElement
from .constants.agent_prompts import ACTION_PLAN_SELECTION_PROMPT
from ..agent.agent_data import AgentData
from ..agent.agent_environment import AgentEnvironment
from ..agent.action_engine import ActionEngine
from ..execution_context import ExecutionContext
from ..services.logging.logging_service import LoggingService
from ..exceptions import MissingAgentGoalsException, MissingMessageException

class AgentElement(BaseElement):
    def __init__(self, name="Unnamed Agent", goals="__agent_goals__", output_var="__payload__", max_iterations=1, context: ExecutionContext = None, agent_data = AgentData(), agent_environment = AgentEnvironment()):
        super().__init__(context=context)

        self.next_action_text = "No action has been determined yet."
        self.llm_provider = OpenAIPromptService()
        self.action_engine = ActionEngine()

        # Set the name of the agent for identification purposes
        self.name = name

        # Set the maximum number of iterations for the agent to perform its tasks
        self.max_iterations = max_iterations

        self.inherited_context = ""  # TODO: change variable name to differentiate between types of 'context'

        self.execution_context = context
        self.execution_id = self.execution_context.execution_id
        self.execution_context.log_info(f"Initializing AgentElement with execution_id: {self.execution_id}")

        self.agent_data = agent_data.set_execution_id(self.execution_id)
        self.agent_environment = agent_environment.set_execution_id(self.execution_id)

        self.goals_var_name = goals
        self.execution_context.log_info(f"Agent goals variable name set to: {self.goals_var_name}")


    def enter(self, message: Message) -> Message:
        if(not message):
            raise MissingMessageException("A valid Message object must be provided to the AgentElement's enter method.")

        self.inherited_context = message.read_context()
        self.mcp_services = message.mcp_services

        goals_value = message.get_var(self.goals_var_name)
        
        if(goals_value):
            self.agent_data.save_goals(goals=goals_value)
            LoggingService.log_info(f"LOADED AGENT GOALS: \n\n  VAR_NAME:\n'{self.goals_var_name}':\n\n  VALUE:\n{goals_value}")
        else:
            raise MissingAgentGoalsException(f"AgentElement '{self.name}' was initialized without goals. Please provide goals via the 'goals' parameter or ensure the variable '{self.goals_var_name}' exists in the message and that it contains non-empty goals.")

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
        next_action_object = self.action_engine.convert_action_text_to_object(action_text=self.next_action_text, execution_context=self.execution_context)
        is_complete = ActionEngine.perform_action(
            action_object=next_action_object,
            execution_context=self.execution_context,
            agent_environment=self.agent_environment,
            agent_data=self.agent_data,
            mcp_services=self.mcp_services
        )
        return (is_complete, message)
    
    def create_generate_plan_prompt(self, message: Message) -> str:
        try:
            goals_text = self.agent_data.get_goals()
            prompt = f"Generate a step-by-step plan to archive the following goals based on the current context and tools available. Remember that you are an intelligent agent who is building a plan for you yourself to follow: {goals_text}"
        except Exception as e:
            error_message = f"An unexpected error occurred when attempting to generate the agent's plan: {e}\n{traceback.format_exc()}"
            raise Exception(error_message)
        return prompt

    def generate_plan(self, message: Message) -> str:
        prompt_text = self.create_generate_plan_prompt(message)
        plan = self.send_llm_request(prompt=prompt_text,message=message)
        self.agent_data.save_plan(plan=plan)
    
    def generate_prompt(self, message: Message=None, prompt: str = "") -> str:
        context_string = self.create_context_string(message)
        full_prompt = f"{context_string}\n\n{prompt}"
        return full_prompt

    def send_llm_request(self, prompt: str = "", message: Message = None) -> str:
        if(prompt == ""):
            self.execution_context.log_warning("No prompt was provided to the LLM request; using empty string as prompt.")

        try:
            full_prompt = self.generate_prompt(message=message, prompt=prompt)
            response = self.llm_provider.ask_question(system="You are an intelligent agent tasked with assisting in the completion of goals based on the provided context and instructions.", question=full_prompt)
        except Exception as e:
            error_message = f"An unexpected error occurred when attempting to send a request to the LLM: {e}\n{traceback.format_exc()}"
            raise Exception(error_message)
        return response
    
    def debug_context_string(self, chat_history = None, goals = None, inherited_context = None, plan = None, services = None, tools = None, working_memory = None) -> str:
        if not inherited_context:
            self.execution_context.log_info("Note: There is no inherited context from previous elements.")
        if not working_memory:
            self.execution_context.log_info("Note: The working memory is currently empty.")
        if not goals:
            self.execution_context.log_error("Note: The current goals are empty.")
        if not plan:
            self.execution_context.log_error("Note: The current plan is empty.")
        if not services:
            self.execution_context.log_warning("Note: There are no services available.")
        if not tools:
            self.execution_context.log_warning("Note: There are no tools available.")
        if not chat_history:
            self.execution_context.log_info("Note: The chat history is currently empty.")

    def create_context_string(self, message: Message) -> str:
        context = ""
        try:
            chat_history = self.agent_data.get_chat_history_summary(message)
            goals = self.agent_data.get_goals()
            inherited_context = self.inherited_context
            plan = self.agent_data.get_plan()
            services = self.agent_data.get_services(message)
            tools = self.agent_data.get_tools(message)
            working_memory = self.agent_data.get_working_memory()

            self.debug_context_string(chat_history, goals, inherited_context, plan, services, tools, working_memory)

            context_parts = [
                "Consider the following when carrying out your tasks: \n",
                f"Log of what has been done so far: {working_memory}\n",
                f" ===== CHAT HISTORY SUMMARY ===== \n {chat_history}\n\n",
                f" ===== ADDITIONAL CONTEXT ===== \n {inherited_context}\n\n",
                f" ===== CURRENT PLAN ===== \n {plan}\n\n",
                f" ===== MCP SERVICE NAMES ===== \n {services}\n\n",
                f" ===== MCP SERVICE TOOLS ===== \n {tools}]\n\n",
                f" ===== GOALS ===== \n {goals}\n\n"
            ]
            context = "\n".join(context_parts)
            self.execution_context.log_info(f"Context for LLM request created...\n\n {context}")
        except Exception as e:
            error_message = f"An unexpected error occurred when attempting to create the context string: {e}\n{traceback.format_exc()}"
            raise Exception(error_message)
        return context

    def get_next_action_text(self, message: Message) -> str:
        response = self.send_llm_request(prompt=ACTION_PLAN_SELECTION_PROMPT, message=message)
        self.execution_context.log_info(f"(chainplate) [NEXT-ACTION-TEXT (should be JSON-parseable):\n\n{response}")
        return response