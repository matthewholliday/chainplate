from ..message import Message
from .ai_base_element import AiBaseElement
from ..helpers.prompt_helper import ask_with_context as prompt_ask

class SendPromptElement(AiBaseElement):
    def __init__(self, name, output_var, content):
        super().__init__(name, output_var, content)

    def enter(self , message: Message) -> Message:
        message = self.try_transform_content(message)
        
        context = message.read_context()
        self.transformed_content = prompt_ask(self.transformed_content, context)        
        
        message = self.try_set_variable(message)
        return message

    def exit(self, message: Message) -> Message:
        return message

    def should_enter(self, message: Message) -> bool:
        return True
    
    def increment_iteration(self, message):
        return message

    def should_exit(self, message: Message) -> tuple[bool, Message]:
        return (True, message)