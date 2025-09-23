from .base_element import BaseElement
from ..message import Message
from ..execution_context import ExecutionContext

class GetContextElement(BaseElement):
    def __init__(self, output_var: str, context: ExecutionContext = None):
        super().__init__(context=context)
        self.output_var = output_var
        self.context = context

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