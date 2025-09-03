from .base_element import BaseElement
from ..message import Message

class ForEachLoopElement(BaseElement):
    """Element for handling foreach loops in the XML interpreter."""
    def __init__(self, output_var: str, input_var: str):
        self.output_var = output_var
        self.input_var = input_var

    def enter(self, message: "Message") -> "Message":
        """Initialize loop variables and prepare for iteration."""
        # Initialize loop variables here if needed
        return message

    def exit(self, message: "Message") -> "Message":
        """Finalize loop processing."""
        # Finalize loop variables here if needed
        return message

    def increment_iteration(self, message: Message) -> Message:
        """Increment the iteration count for the foreach loop."""
        # Logic to increment the iteration count
        return message