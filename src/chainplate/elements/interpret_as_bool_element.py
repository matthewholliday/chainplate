from .interpret_as_base_element import InterpretAsBase

TEMPLATE_TEXT = """
You are a strict boolean interpreter.

Goal: Examine the provided content and decide whether it represents TRUE or FALSE.

Content:
{{ input_txt | trim }}

Instructions:
- Output EXACTLY one token: True or False. No quotes, punctuation, explanations, code fences, or extra text.
- Be case-insensitive when interpreting the content.
- True if the content clearly affirms or is a standard truthy value:
  - "true", "t", "yes", "y", "1", "on", "enabled", "enable", "allowed", "allow", "active", "affirmative", "correct", "success", "pass", "checked"
- False if the content clearly negates or is a standard falsy/empty value:
  - "false", "f", "no", "n", "0", "off", "disabled", "disable", "denied", "deny", "inactive", "negative", "incorrect", "failure", "fail", "error", "unchecked", "null", "none", "nil", "n/a", "undefined", "blank", "empty"
- Numeric strings: 0 ⇒ False; any non-zero number ⇒ True.
- Sentences/phrases: decide the overall meaning (affirmation ⇒ True, negation/absence ⇒ False). Negation words (e.g., "not", "never", "no", "without", "cannot", "disable") indicate False.
- If the meaning is mixed, contradictory, or uncertain, default to False.

Answer with only:
True
or
False

"""

class InterpretAsBoolElement(InterpretAsBase):
    def __init__(self,output_var, input_var):
        super().__init__(output_var, input_var)

    def get_prompt_template(self):
        return TEMPLATE_TEXT
    
    def get_label(self) -> str:
        return f"InterpretAsBoolElement(output_var={self.output_var}, input_var={self.input_var})"
    
    def get_tag(self) -> str:
        return "interpret-as-bool"