from abc import ABC, abstractmethod
from ..message import Message
from ..helpers.template_helper import TemplateHelper2

class BaseElement(ABC):
    """Abstract base class for all elements in the XML interpreter."""

    @abstractmethod
    def enter(self, message: "Message") -> "Message":
        """Called when entering the element."""
        pass

    @abstractmethod
    def exit(self, message: "Message") -> "Message":
        """Called when exiting the element."""
        pass

    # concrete methods...
    def should_enter(self, message: Message) -> bool:
        return True
    
    def increment_iteration(self, message):
        return message

    def should_exit(self, message: Message) -> tuple[bool, Message]:
        return (True, message)
    
    def apply_template(self, template_str: str, message: Message) -> str:
        context = message.get_vars()
        rendered_content = TemplateHelper2.render_template(template_str, context)
        return rendered_content
    
    def get_collection(self, message: Message) -> list:
        return None
    
    def get_current_item(self) -> str:
        return None
    
    def update_content(self, new_content: str) -> None:
        pass