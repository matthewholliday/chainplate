from ..message import Message
from .template_helper import TemplateHelper

class BooleanHelper:
    TRUE_VALUES = {"true", "1", "yes", "on"}
    FALSE_VALUES = {"false", "0", "no", "off"}

    @staticmethod
    def to_bool(value: str) -> bool:
        value_lower = value.strip().lower()
        if value_lower in BooleanHelper.TRUE_VALUES:
            return True
        elif value_lower in BooleanHelper.FALSE_VALUES:
            return False
        else:
            raise ValueError(f"Cannot interpret '{value}' as boolean.")
        
    @staticmethod
    def is_bool(value: str) -> bool:
        value_lower = value.strip().lower()
        return value_lower in BooleanHelper.TRUE_VALUES or value_lower in BooleanHelper.FALSE_VALUES
    
    @staticmethod
    def is_true(value: str) -> bool:
        value_lower = value.strip().lower()
        return value_lower in BooleanHelper.TRUE_VALUES
    
    @staticmethod
    def is_false(value: str) -> bool:
        value_lower = value.strip().lower()
        return value_lower in BooleanHelper.FALSE_VALUES
    
    @staticmethod
    def evaluate_condition(condition: str, message: Message) -> bool:
        rendered = TemplateHelper.render_template(condition, message.get_vars())
        return BooleanHelper.to_bool(rendered)