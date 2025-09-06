from .interpret_as_base_element import InterpretAsBase

TEMPLATE_TEXT = """
You are an assistant. You will be given some instructions in the {{ input_text }} merge field. Your only task is to determine the JSON object that should be sent to the MCP tool according to those instructions. Output only the JSON object, with no explanation, formatting, or extra text. If no JSON object is specified, output nothing.
"""

class MCPExtractPayload(InterpretAsBase):
    def __init__(self,output_var, input_var):
        super().__init__(output_var, input_var)

    def get_prompt_template(self):
        return TEMPLATE_TEXT