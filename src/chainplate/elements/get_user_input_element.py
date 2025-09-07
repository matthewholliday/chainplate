from ..message import Message
from .base_element import BaseElement

class GetUserInputElement(BaseElement):
    def __init__(self, output_var, content):

        #TODO: come up with better defaults...
        self.output_var = "unnamed" if output_var is None else output_var
        self.content = content

    def enter(self , message: Message) -> Message:
        self.content = self.apply_templates([self.content], message)[0]

        message = message.set_var(self.output_var, self.content)

        user_input = input(self.content)
        message = message.set_var(self.output_var, user_input)

        return message

    def exit(self, message: Message) -> Message:
        return message
    
    def get_label(self) -> str:
        return f"GetUserInputElement(output_var={self.output_var}, content={self.content})"
    
    def get_tag(self) -> str:
        return "get-user-input"