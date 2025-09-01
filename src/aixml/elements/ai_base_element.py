from ..message import Message
from ..helpers.template_helper import TemplateHelper
from abc import ABC, abstractmethod

class AiBaseElement(ABC):
    def __init__(self, name, output_var, content):
        self.name = "unnamed" if name is None else name
        self.output_var = "unnamed" if output_var is None else output_var
        self.content = content
        self.transformed_content = None

    @abstractmethod
    def enter(self , message: Message) -> Message:
        pass

    @abstractmethod
    def exit(self, message: Message) -> Message:
        return message
    
    def try_transform_content(self, message: Message) -> Message:
        if self.transformed_content is None and self.content:
            if message.has_template_bindings(self.content):
                self.transformed_content = TemplateHelper.render_template(template_str=self.content, context=message.get_vars())
            else:
                self.transformed_content = self.content
        return message
    
    def try_set_variable(self, message: Message) -> Message:
        if self.output_var and self.content:
            message = message.set_var(self.output_var, self.transformed_content)
        return message
    
    def conditions_passed(self, message: Message) -> bool:
        return True