from .base_element import BaseElement
from ..message import Message
from ..services.external.prompt_completion_services.openai_llm_provider import OpenAIPromptService

class AgentElement(BaseElement):
    def __init__(self, name="Unnamed Agent", goals="default_goal_var", max_iterations=1):
        super().__init__()

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
        return message

    def exit(self, message) -> Message:
        print(f"Exiting AgentElement '{self.name}' with the following state:")
        print(f"  Goals: {self.goals_text}")
        print(f"  Plan: {self.plan_text}")
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
        return self.send_llm_request(message=message,prompt="Generate a step-by-step plan to achive the following goals based on the current context and tools available.")
    
    def send_llm_request(self, message: Message, prompt: str) -> str:
        context_string = self.create_context_string(message)
        full_prompt = f"{context_string}\n\n{prompt}"
        response = self.llm_provider.ask_question(system="You are an intelligent agent tasked with assisting in the completion of goals based on the provided context and instructions.", question=full_prompt)
        return response
    
    def create_context_string(self, message: Message) -> str:
        context_parts = [
            "Consider the following when carrying out your tasks: \n",
            f"Log of actions taken by you so far: {self.agent_log_text}\n",
            f"Your current goals are: {self.goals_text}\n",
            f"Your current plan (if any) is: {self.plan_text}\n",
            "Based on the above information, please with your instructions(see below):\n"
        ]
        return "\n".join(context_parts)
    
    def get_master_tool_overview_text(self, message: Message) -> str:
        mcp_services = message.get_mcp_services()
        tools_text = ""
        for mcp_service in mcp_services.values():
            for tool_name, tool_data in mcp_service.tools.items():
                tools_text += f"{tool_name} ({tool_data['description']})\n"
        return tools_text.strip()

    
