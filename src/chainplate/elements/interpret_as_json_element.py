"""
Element: interpret-as-json
Description: Interprets the input payload as JSON using the naive_datatype_service.
"""
from ..services.naive_datatype_service import NaiveDatatypeService
from ..ainode import register_element


class InterpretAsJsonElement:
    tag = "interpret-as-json"

    def __init__(self, output_var=None, input_var=None, node=None, **kwargs):
        self.node = node
        self.output_var = output_var
        self.input_var = input_var
        self.service = NaiveDatatypeService()

    def execute(self, message):
        # Use input_var from message.variables if available, else fallback to payload
        payload = message.variables.get(self.input_var) if self.input_var and hasattr(message, 'variables') and message.variables else message.payload
        try:
            json_data = self.service.interpret_as_json(payload)
            if self.output_var and hasattr(message, 'variables') and message.variables is not None:
                message.variables[self.output_var] = json_data
            else:
                message.payload = json_data
            message.status = "success"
        except Exception as e:
            message.status = "error"
            message.error = str(e)
        return message

register_element(InterpretAsJsonElement.tag, InterpretAsJsonElement)
