from ..message import Message
from ..helpers.template_helper import TemplateHelper
from .base_element import BaseElement

class ContinueIfElement(BaseElement):
    def __init__(self, condition: str, output_var=None):
        self.condition = condition
        self.output_var = output_var

    def enter(self, message:Message) -> Message:
        return message

    def exit(self, message:Message) -> Message:
        return message
    
    def should_enter(self, message: Message) -> bool:
        print("Evaluating ContinueIf condition...")

        conditions_passed = False

        evaluation = TemplateHelper.render_template(self.condition, message.get_vars())

        if evaluation.strip().lower() in ["true", "1", "yes"]:
            conditions_passed = True
        
        message.set_var(self.output_var, conditions_passed)

        return conditions_passed