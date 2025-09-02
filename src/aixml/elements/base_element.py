from abc import ABC, abstractmethod
from ..message import Message
from ..message_update import MessageUpdate

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