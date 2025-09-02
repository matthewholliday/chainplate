from ..message import Message
from .base_element import BaseElement

class PipelineElement(BaseElement):
    def __init__(self, name):
        self.name = name

    def enter(self, message:Message) -> Message:
        return message

    def exit(self, message:Message) -> Message:
        return message
    
    def conditions_passed(self, message: Message) -> bool:
        return True