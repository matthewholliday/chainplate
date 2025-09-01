from ..message import Message
from ..helpers.template_helper import TemplateHelper
from abc import ABC, abstractmethod
from ..helpers.prompt_helper import ask as prompt_ask

class InterpretAsBase(ABC):
    def __init__(self, name, output_var, input_var):
        self.name = "unnamed" if name is None else name
        self.output_var = "unnamed" if output_var is None else output_var
        self.input_var = "unnamed" if input_var is None else input_var
        self.transformed_prompt = None
        self.input_value = None
        self.template_text = None
        self.response_text = None

    @abstractmethod
    def get_prompt_template(self) -> str:
        pass

    @abstractmethod
    def get_template_context() -> dict: 
        pass   

    def enter(self , message: Message) -> Message:
        self.input_value = message.get_var(self.input_var)
        self.template_text = self.get_prompt_template()
        self.try_apply_template()
        self.response_text = message.prompt_ask(self.transformed_prompt)
        message = self.try_set_variable(message)
        return message

    def exit(self, message: Message) -> Message:
        return message
    
    def try_apply_template(self) -> Message:
        self.transformed_prompt = TemplateHelper.render_template(template_str=self.template_text, context=self.get_template_context())

    def try_set_variable(self, message: Message) -> Message:
        if self.output_var and self.response_text:
            message = message.set_var(self.output_var, self.response_text)
        return message
    
    def conditions_passed(self, message: Message) -> bool:
        return True
    
    