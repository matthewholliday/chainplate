from ..message import Message
from .base_element import BaseElement

class ContextElement(BaseElement):
    def __init__(self, content: str):
        self.content = content

    def enter(self, message:Message) -> Message:

        # Apply templating to the content
        self.content = self.apply_template(self.content,message)

        # Push a new context onto the message stack
        message.push_context(content=self.content)
        return message

    def exit(self, message:Message) -> Message:

        # Pop the context from the message stack when the block ends
        message.pop_context()
        return message
    
    def conditions_passed(self, message: Message) -> bool:
        return True