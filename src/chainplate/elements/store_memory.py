from .base_element import BaseElement
from ..message import Message
from ..services.memory_service import MemoryService

class StoreMemory(BaseElement):
    def __init__(self, input_var: str, content: str):
        self.input_var = input_var
        self.content = content

    def enter(self,message: Message) -> Message:
        value = self.get_value(message)
        MemoryService().create_memory(value)
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
