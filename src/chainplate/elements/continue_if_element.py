from ..message import Message
from ..helpers.template_helper import TemplateHelper
from .base_element import BaseElement
from ..helpers.boolean_helper import BooleanHelper

class ContinueIfElement(BaseElement):
    def __init__(self, condition: str, output_var=None):
        self.condition = condition
        self.output_var = output_var

    def enter(self, message:Message) -> Message:
        return message

    def exit(self, message:Message) -> Message:
        return message
    
    def should_enter(self, message: Message) -> bool:
        # Apply templating to condition and output_var
        self.condition, self.output_var = self.apply_templates([self.condition, self.output_var], message)

        # Evaluate the condition
        conditions_passed = False

        try:
            conditions_passed = BooleanHelper.evaluate_condition(self.condition, message)
        except ValueError:
            conditions_passed = False
            raise ValueError(f"Cannot interpret condition '{self.condition}' as boolean.")
        
        message.set_var(self.output_var, conditions_passed)

        return conditions_passed
    
    def get_label(self) -> str:
        return f"ContinueIfElement(condition={self.condition}, output_var={self.output_var})"
    
    def get_tag(self) -> str:
        return "continue-if"