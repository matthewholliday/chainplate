from ..message import Message
from ..helpers.template_helper import TemplateHelper
from abc import ABC, abstractmethod

class AiBaseElement(ABC):
    def __init__(self, name, output_var, content):
        self.name = "unnamed" if name is None else name
        self.output_var = "unnamed" if output_var is None else output_var
        self.content = content
        self.original_content = content

    @abstractmethod
    def enter(self , message: Message) -> Message:
        pass

    @abstractmethod
    def exit(self, message: Message) -> Message:
        return message
    
    def conditions_passed(self, message: Message) -> bool:
        return True