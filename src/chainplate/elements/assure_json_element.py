from ..services.naive_datatype_service import NaiveDataTypeService
from .base_element import BaseElement

class AssureJsonElement(BaseElement):
    def __init__(self, output_var: str, input_var: str, max_attempts = 5):
        super().__init__()
        self.output_var = output_var
        self.input_var = input_var
        self.datatype_service = NaiveDataTypeService()
        self.max_attempts = max_attempts

    def enter(self, message):
        input_value = message.get_var(self.input_var)
        try:
            json_output = self.datatype_service.to_json_with_retry(
                payload=input_value,
                max_retries=self.max_attempts
            )
        except ValueError as e:
            message.set_var(self.output_var, "Error converting to JSON: " + str(e))
        
        return message.set_var(self.output_var, json_output)
    
    def exit(self, message):
        return message


