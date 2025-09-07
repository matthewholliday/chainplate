from .base_element import BaseElement
from ..message import Message

class GetContextElement(BaseElement):
    def __init__(self, output_var: str):
        self.output_var = output_var

    def enter(self, message: Message) -> Message:
        context_data = message.read_context()
        message.set_var(self.output_var, context_data)
        return message

    def exit(self, message: Message) -> Message:
        return message
    
    def get_label(self) -> str:
        return f"GetContextElement(output_var={self.output_var})"
    
    @staticmethod
    def get_tag() -> str:
        return "get-context"