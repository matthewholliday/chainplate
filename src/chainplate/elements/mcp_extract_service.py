from .interpret_as_base_element import InterpretAsBase

TEMPLATE_TEXT = """
You are an assistant. You will be given some instructions in the {{ input_text }} merge field. Your only task is to determine the name of the MCP service that those instructions reference. Output only the exact name of the MCP service, with no explanation, formatting, or extra text. If no service is specified, output nothing.
"""

class MCPExtractService(InterpretAsBase):
    def __init__(self,output_var, input_var):
        super().__init__(output_var, input_var)

    def get_prompt_template(self):
        return TEMPLATE_TEXT