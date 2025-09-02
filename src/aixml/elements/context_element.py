from ..message import Message
from .base_element import BaseElement

class ContextElement(BaseElement):
    def __init__(self, name, content: str):
        self.name = name
        self.content = content

    def enter(self, message:Message) -> Message:
        message.push_context(content=self.content)
        return message

    def exit(self, message:Message) -> Message:
        message.pop_context()
        return message
    
    def conditions_passed(self, message: Message) -> bool:
        return True