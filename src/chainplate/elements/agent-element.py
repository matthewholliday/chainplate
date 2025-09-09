from .base_element import BaseElement
from ..agent.agent import Agent
from ..message import Message

class AgentElement(BaseElement):
    def __init__(self, name="Unnamed Agent",goals="default_goal_var", plan="default_plan_var"):
        super().__init__()

        #set the name of the agent for identification purposes
        self.name = name

        #set variable names for goals and plan to be used in the message vars
        self.goals_var_name = goals
        self.plan_var_name = plan

        #initialize the agent instance
        self.agent = Agent()

    def enter(self, message):
        mcp_services = message.mcp_services
        message.add_agent(self.agent)
        return message

    def exit(self, message):
        message.clear_agent()
        return message
    
    @staticmethod
    def get_tag() -> str:
        return "agent"
    
    def get_label(self) -> str:
        return f"AgentElement(name={self.name})"
    
    def update_plan(self, message: Message, plan_text: str) -> "AgentElement":
        message.set_var(self.plan_var_name, plan_text)
        return self
    
    def get_current_plan(self, message: Message) -> str:
        return message.get_var(self.plan_var_name)
    
    def update_goals(self, message: Message, goals_text: str) -> "AgentElement":
        message.set_var(self.goals_var_name, goals_text)
        return self
    
    def get_current_goals(self, message: Message) -> str:
        return message.get_var(self.goals_var_name)