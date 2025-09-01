from ..helpers.template_helper import TemplateHelper
from .interpret_as_base_element import InterpretAsBase

TEMPLATE_TEXT = """
    You are a meticulous, pragmatic classifier.

    ## Inputs
    - Categories (choose only from this list): {{ categories | join(', ') }}
    - Content: {{ input_text }}
    - Classification criteria: {{ criteria }}

    ## Task
    From the provided **Categories**, select every category that is applicable to the **Content**, using the **criteria**. Make reasonable assumptions where information is implicit, but do not invent new categories or reword existing ones.

    ## Decision rules
    - Prefer recall over precision when the criteria suggest ambiguity; include a category if the content likely fits based on reasonable inference.
    - Respect exclusions or thresholds stated in the criteria.
    - Keep the original casing and spelling of categories exactly as shown in the list.
    - Do not include duplicates.
    - If none apply, output nothing (i.e., an empty string).

    ## Output format (strict)
    Output **only** a comma-delimited list of the applicable categories, unquoted, with no spaces before/after commas, and nothing else.  
    No explanations, no bullets, no prose, no headers.

    ## Now output the result:
"""

class ClassifyExclusive(InterpretAsBase):
    def __init__(self, name, output_var, input_var, categories, criteria):
        super().__init__(name, output_var, input_var)
        self.categories = categories
        self.criteria = criteria

    def get_prompt_template(self):
        return TEMPLATE_TEXT
    
    def get_categories_as_list(self):
        return [c.strip() for c in self.categories.split(",") if c.strip()]
    
    def get_template_context(self):
        return { "input_text": self.get_input_value(), "categories": self.get_categories_as_list(), "criteria": self.criteria }