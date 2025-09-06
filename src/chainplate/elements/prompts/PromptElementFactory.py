from ..send_prompt_element import SendPromptElement
from ..interpret_as_bool_element import InterpretAsBoolElement

class PromptElementFactory:
    @staticmethod
    def create_element(output_var: str, content: str):
        return SendPromptElement(output_var=output_var, content=content)