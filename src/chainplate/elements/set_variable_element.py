from ..message import Message
from .base_element import BaseElement
from ..helpers.template_helper import TemplateHelper

class SetVariableElement(BaseElement):
    def __init__(self, output_var, content):

        #TODO: come up with better defaults...
        self.output_var = "unnamed" if output_var is None else output_var
        self.content = content

    def enter(self , message: Message) -> Message:
        content = TemplateHelper.safe_render_template(template_str=self.content, template_context=message.vars)
        message = message.set_var(self.output_var, content)
        return message

    def exit(self, message: Message) -> Message:
        return message
    
    def get_label(self) -> str:
        return f"SetVariableElement(output_var={self.output_var}, content={self.content})"
    
    def get_tag(self):
        return "set-variable"