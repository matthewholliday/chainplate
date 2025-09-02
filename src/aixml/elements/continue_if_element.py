from ..message import Message
from ..helpers.template_helper import TemplateHelper
from .base_element import BaseElement

class ContinueIfElement(BaseElement):
    def __init__(self, name, condition: str, output_var=None):
        self.name = name
        self.condition = condition
        self.output_var = output_var
        self

    def enter(self, message:Message) -> Message:
        message = message.log_continue_if_start(self.name,self.condition,self.output_var) #TODO: migrate to LoggingHelper
        return message

    def exit(self, message:Message) -> Message:
        message = message.log_continue_if_end(self.name,self.condition,self.output_var) #TODO: migrate to LoggingHelper
        return message
    
    def should_enter(self, message: Message) -> bool:
        print("Evaluating ContinueIf condition...")

        conditions_passed = False

        evaluation = TemplateHelper.render_template(self.condition, message.get_vars())

        if evaluation.strip().lower() in ["true", "1", "yes"]:
            conditions_passed = True
        
        message.set_var(self.output_var, conditions_passed)

        return conditions_passed