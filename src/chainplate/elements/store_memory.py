from .base_element import BaseElement
from ..message import Message
from ..services.memory_service import MemoryService

class StoreMemory(BaseElement):
    PREFIX = "Here is a more recent memory that has been stored in the system. Please use this information to inform your responses and actions: "

    def __init__(self, input_var: str, content: str):
        self.input_var = input_var
        self.content = content

    def enter(self,message: Message) -> Message:
        value = self.PREFIX + self.get_value(message)
        MemoryService().create_memory(value)
        message.push_context(content=self.content)
        return message
    
    def exit(self,message: Message) -> Message:
        return message

    def get_value(self, message: Message) -> str:
        retrieved_value = ""
        if self.input_var:
            retrieved_value = message.get_var(self.input_var)
        elif self.content:
            retrieved_value = self.content
        return retrieved_value
