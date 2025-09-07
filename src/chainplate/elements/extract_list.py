from .interpret_as_base_element import InterpretAsBase

TEMPLATE_TEXT = """
    You are a meticulous, pragmatic extractor.

    ## Inputs
    - Source text: {{ input_text }}
    - Extraction criteria: {{ criteria }}

    ## Task
    From the **Source text**, extract a list of items that meet the **Extraction criteria**.  
    Make reasonable assumptions where information is implicit, but do not invent items or reword them.

    ## Decision rules
    - Prefer recall over precision when the criteria suggest ambiguity; include an item if the content likely fits.
    - Respect exclusions or thresholds stated in the criteria.
    - Keep the original casing and spelling exactly as in the text.
    - Do not include duplicates.
    - If no items apply, output nothing (i.e., an empty string).

    ## Output format (strict)
    Output **only** a comma-delimited list of items, unquoted, with no spaces before/after commas, and nothing else.  
    No explanations, no bullets, no prose, no headers.

    ## Now output the result:
"""

class ExtractList(InterpretAsBase):
    def __init__(self, output_var, input_var, criteria, content):
        super().__init__(output_var, input_var)
        self.criteria = criteria
        self.content = content

    def get_prompt_template(self):
        return TEMPLATE_TEXT
    
    def get_template_context(self):
        return { 
            "input_text": self.get_input_text(), 
            "criteria": self.criteria 
        }
    
    def get_input_text(self):
        # Use the content directly as the input text
        return self.content if self.content else self.get_input_value()
    
    def get_label(self) -> str:
        return f"ExtractList(output_var={self.output_var}, input_var={self.input_var}, criteria={self.criteria})"
    
    @staticmethod
    def get_tag() -> str:
        return "extract-list"
