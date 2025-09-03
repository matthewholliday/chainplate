from ..message import Message
from .base_element import BaseElement
from abc import abstractmethod

from ..helpers.template_helper import TemplateHelper
from ..helpers.prompt_helper import ask as ask_ai


class InterpretAsBase(BaseElement):
    def __init__(self, output_var, input_var):
        self.output_var = "unnamed" if output_var is None else output_var
        self.input_var = "unnamed" if input_var is None else input_var

    def enter(self , message: Message) -> Message:

        # Get the input value from the message variables
        self.input_value = message.get_var(self.input_var)

        # Get the prompt template string provided by the concrete class
        template_text: str = self.get_prompt_template()

        # Get the context for rendering the template, provided by the concrete class
        template_context: dict = self.get_template_context()

        # Render the prompt template with the context
        rendered_text: str = TemplateHelper.safe_render_template(template_str=template_text, template_context=template_context)

        # Send the rendered text to the AI and get the response
        response: str = ask_ai(rendered_text)

        # Store the response in the specified output variable
        message.set_var(self.output_var, response)

        # Also set the special __payload__ variable
        message.set_payload(response)
        
        return message

    def exit(self, message: Message) -> Message:
        return message
    
    def get_input_value(self):
        return self.input_value
    
    # Note: by default, "input_var" is the name of the input variable. Concrete classes can override this if needed.
    def get_template_context(self):
        return { "input_txt" : self.get_input_value() }
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        pass 
    
    