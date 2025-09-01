from ..message import Message
from ..helpers.boolean_helper import BooleanHelper
from .base_element import BaseElement

class ForLoopElement(BaseElement):
    def __init__(self, name: str, start_num: int, stop_num: int):
        self.name = name
        self.is_repeating = True
        self.current_iteration = start_num
        self.stop_num = stop_num

    def enter(self, message: Message) -> Message:
        return message
    
    def exit(self, message: Message) -> Message:
        return message

    def increment_iteration(self, message: Message) -> Message:
        self.current_iteration += 1
        message.set_var("index", self.current_iteration)
        return message

    def should_exit(self, message: Message) -> tuple[bool, Message]:
        result: bool = False
        
        try:
            result = self.current_iteration < self.stop_num
            return (result == False, message) # Exit if condition is false
        except Exception as e:
            return (True, message.log_message(f"ForLoopElement '{self.name}' encountered an error: {e}")) # Stop on error