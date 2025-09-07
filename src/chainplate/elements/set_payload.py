from .base_element import BaseElement
from ..message import Message

class SetPayloadElement(BaseElement):
    def __init__(self, input_var: str = "", content: str = ""):
        self.input_var = input_var
        self.content = content

    def enter(self, message: Message) -> Message:
        value = self.get_input_value(message, self.input_var, self.content)
        message.set_var("__payload__", value) #TODD - consolidate magic strings into a constants file or class
        return message

    def exit(self, message: Message) -> Message:
        return message
    
    def get_input_value(self, message: Message, input_var: str, content: str) -> str:
        if input_var:
            return message.get_var(input_var)
        elif content:
            return content
        else:
            raise ValueError("Either 'input_var' or 'content' must be provided to get the input value.")
    
    def get_payload(self, message: Message) -> str:
        return message.get_var("__payload__")
    
    def get_label(self) -> str:
        return f"SetPayloadElement(input_var={self.input_var}, content={self.content})"
    
    def get_tag(self) -> str:
        return "set-payload"