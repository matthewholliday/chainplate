from ..message import Message
from .ai_base_element import AiBaseElement
from ..helpers.prompt_helper import ask_with_context
from ..helpers.template_helper import TemplateHelper

class SendPromptElement(AiBaseElement):
    def __init__(self, name, output_var, content):
        super().__init__(name, output_var, content)

    def enter(self , message: Message) -> Message:
        # Render the content as a template using message.vars as the template context
        templated_content= TemplateHelper.safe_render_template(template_str=self.content, template_context=message.get_vars())

        # Set the special __chat_input__ variable
        message.set_chat_input(templated_content)

        # Get the current context from the message
        context = message.read_context()
        
        chat_history = message.get_chat_history()

        # Send the prompt and get the response
        response = ask_with_context(templated_content, context, chat_history)

        # Store the response in the specified output variable     
        message.set_var(self.output_var, response)

        # Also set the special __payload__ variable
        message.set_payload(templated_content)

        # Also set the special __chat_response__ variable
        message.set_chat_response(response)

        return message

    def exit(self, message: Message) -> Message:
        return message

    def should_enter(self, message: Message) -> bool:
        return True
    
    def increment_iteration(self, message):
        return message

    def should_exit(self, message: Message) -> tuple[bool, Message]:
        return (True, message)