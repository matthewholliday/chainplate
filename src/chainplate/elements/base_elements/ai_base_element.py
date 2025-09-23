from ...message import Message
from ...helpers.template_helper import TemplateHelper
from abc import abstractmethod
from ..base_element import BaseElement
from ...execution_context import ExecutionContext

class AiBaseElement(BaseElement):
    def __init__(self, output_var, content, context: ExecutionContext = None):
        super().__init__(context=context)
        self.output_var = "unnamed" if output_var is None else output_var
        self.content = content
        self.original_content = content
        self.context = context

    @abstractmethod
    def enter(self , message: Message) -> Message:
        #self.output_var, self.content, self.original_content = self.apply_templates([self.output_var, self.content, self.original_content], message)
        self.output_var = self.apply_template(self.output_var, message)
        self.content = self.apply_template(self.content, message)

    @abstractmethod
    def exit(self, message: Message) -> Message:
        return message
    
    def conditions_passed(self, message: Message) -> bool:
        return True