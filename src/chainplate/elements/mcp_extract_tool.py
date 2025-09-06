from .interpret_as_base_element import InterpretAsBase

TEMPLATE_TEXT = """
You are an assistant. You will be given some instructions. Your only task is to determine which MCP tool those instructions say should be called. Output only the exact name of that MCP tool, with no explanation, formatting, or extra text. If no tool is specified, output nothing. 

Here are the instructions:

 {{ input_text }}
"""

class MCPExtractTool(InterpretAsBase):
    def __init__(self,output_var, input_var):
        super().__init__(output_var, input_var)

    def get_prompt_template(self):
        return TEMPLATE_TEXT