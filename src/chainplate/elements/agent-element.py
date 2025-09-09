from .base_element import BaseElement
from ..agent.agent import Agent

class AgentElement(BaseElement):
    def __init__(self, name="Unnamed Agent"):
        super().__init__()
        self.name = name
        self.agent = Agent()

    def enter(self, message):
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