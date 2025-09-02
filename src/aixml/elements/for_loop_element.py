from ..message import Message
from ..helpers.boolean_helper import BooleanHelper
from .base_element import BaseElement

class ForLoopElement(BaseElement):
    def __init__(self, start_num: str, stop_num: str):
        self.is_repeating = True
        
        self.current_iteration_str = start_num
        self.stop_num_str = stop_num

        self.stop_num_int = None
        self.current_iteration_int = None
        
        self.current_iteration_evaluated = ""
        self.stop_num_evaluated = ""

    def enter(self, message: Message) -> Message:
        try:
            self.current_iteration_evaluated, self.stop_num_evaluated = self.apply_templates(templates=[self.current_iteration_str, self.stop_num_str], message=message)
            self.current_iteration_int = int(self.current_iteration_evaluated)
            self.stop_num_int = int(self.stop_num_evaluated)
        except Exception as e:
            error_message = f"ForLoopElement encountered an error during evaluation: {e}"
            return message.log_message(error_message)
        return message
    
    def exit(self, message: Message) -> Message:
        return message

    def increment_iteration(self, message: Message) -> Message:
        self.current_iteration_int += 1
        message.set_var("index", self.current_iteration_int)
        return message

    def should_exit(self, message: Message) -> tuple[bool, Message]:
        result: bool = False
        
        try:
            result = self.current_iteration_int < self.stop_num_int
            return (result == False, message) # Exit if condition is false
        except Exception as e:
            return (True, message.log_message(f"ForLoopElement encountered an error: {e}")) # Stop on error