from .base_element import BaseElement
from ..message import Message
from ..helpers.list_helper import ListHelper

class ForEachLoopElement(BaseElement):
    """Element for handling foreach loops in the XML interpreter."""
    def __init__(self, output_var: str, input_var: str):
        self.is_repeating = True
        self.output_var = output_var
        self.input_var = input_var
        self.collection = []
        self.index = 0

    def enter(self, message: Message) -> Message:
        """Initialize the loop by retrieving the collection from the input variable."""
        collection = self.get_collection(message)
        if not collection:
            raise ValueError(f"No collection found for input variable '{self.input_var}'")
        
        self.collection = collection
        return message
    
    def exit(self, message: Message) -> Message:
        return message
    
    def should_enter(self, message):
        collection = self.get_collection(message)
        return self.index < len(collection)

    def get_collection(self, message: Message) -> list:
        """Retrieve the collection from the input variable."""
        input_var_value = message.get_var(self.input_var)
        return ListHelper.get_list_from_string(input_var_value)
    
    def get_current_item(self) -> str:
        index = self.index
        """Get the current item from the collection based on the index."""
        if index < 0 or index >= len(self.collection):
            raise IndexError(f"Index {index} out of range for collection of length {len(self.collection)}")
        return self.collection[index]
    
    def increment_iteration(self, message) -> None:
        """Increment the index for the next iteration. Does nothing if already at end."""
        if self.index < len(self.collection):
            self.index += 1
        message.set_var(self.output_var, self.get_current_item())
        return message
    
    def should_exit(self, message):
        return (self.index >= len(self.collection) - 1,message)
    
    def get_label(self) -> str:
        return f"ForEachLoopElement(output_var={self.output_var}, input_var={self.input_var})"
    
    @staticmethod
    def get_tag() -> str:
        return "foreach-loop"


