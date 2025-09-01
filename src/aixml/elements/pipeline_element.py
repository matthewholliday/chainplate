from ..message import Message
from .base_element import BaseElement

class PipelineElement(BaseElement):
    def __init__(self, name):
        self.name = name

    def enter(self, message:Message) -> Message:
        message = message.log_pipeline_start(self.name)
        return message

    def exit(self, message:Message) -> Message:
        message = message.log_pipeline_end(self.name)
        return message
    
    def conditions_passed(self, message: Message) -> bool:
        return True