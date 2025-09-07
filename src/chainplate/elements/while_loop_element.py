from ..message import Message
from ..helpers.boolean_helper import BooleanHelper
from .base_element import BaseElement

class WhileLoopElement(BaseElement):
    def __init__(self,condition: str):
        self.condition = condition
        self.is_repeating = True

    def enter(self, message: Message) -> Message:
        return message
    
    def exit(self, message: Message) -> Message:
        return message

    def should_exit(self, message: Message) -> tuple[bool, Message]:
        result: bool = False
        
        try:
            result = BooleanHelper.evaluate_condition(self.condition, message)
            return (result == False, message) # Exit if condition is false
        except Exception as e:
            return (True, message.log_message(f"WhileLoopElement '{self.name}' encountered an error: {e}")) # Stop on error
        
    def get_label(self) -> str:
        return f"WhileLoopElement(condition={self.condition})"
    
    def get_tag(self) -> str:
        return "while-loop"