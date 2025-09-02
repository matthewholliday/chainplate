from ..message import Message
from ..helpers.template_helper import TemplateHelper
from .interpret_as_base_element import InterpretAsBase

TEMPLATE_TEXT = """
You are a precise integer interpreter. Convert the given input into a single integer using the best available information.

Input: "{{ input_txt | trim }}"

Rules:
- Output MUST be only the integer: ASCII digits with an optional leading "-" for negatives. No spaces, commas, units, words, or extra characters.
- Normalize and interpret common forms:
  - Ignore thousands separators, currency/percent symbols, and surrounding text.
  - If a decimal is present, round to the nearest integer (0.5 rounds away from zero).
  - Convert number words (e.g., "forty-two", "three thousand") to digits.
  - Expand magnitude suffixes: k = ×1,000; m/mb/mil = ×1,000,000; b/bn = ×1,000,000,000 (case-insensitive).
  - Handle scientific notation (e.g., 1e3 → 1000).
  - For ranges (e.g., "3–5", "3 to 5"), return the midpoint rounded to the nearest integer.
- If multiple quantities occur, return the one that most directly represents the value implied by the input (ignore IDs, dates, addresses, product codes).
- No leading zeros (except for zero itself).
- If no reasonable integer can be determined, return nothing.

Now output exactly the integer and nothing else.

"""

class InterpretAsIntegerElement(InterpretAsBase):
    def __init__(self, name, output_var, input_var):
        super().__init__(name, output_var, input_var)

    def get_prompt_template(self):
        return TEMPLATE_TEXT