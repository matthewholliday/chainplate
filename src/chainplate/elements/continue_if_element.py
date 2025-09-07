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
        evaluation_result = self.apply_template(self.condition, message)

        # Evaluate the condition
        conditions_passed = False

        try:
            conditions_passed = BooleanHelper.evaluate_condition(evaluation_result, message)
        except ValueError:
            conditions_passed = False
            raise ValueError(f"Cannot interpret condition '{self.condition}' as boolean.")
        
        message.set_var(self.output_var, conditions_passed)

        return conditions_passed