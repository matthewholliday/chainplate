from ..message import Message
from .base_elements.ai_base_element import AiBaseElement
from ..helpers.prompt_helper import ask_with_context, ask_with_context_and_spinner
from ..helpers.template_helper import TemplateHelper2

class SendPromptElement(AiBaseElement):
    def __init__(self, output_var, content):
        super().__init__(output_var, content)

    def enter(self , message: Message) -> Message: #test please
        message.set_var("__chat_input__",message.get_payload())  # Set the special __chat_input__ variable to the current payload

         # This will template output_var and content
        super().enter(message)

        # Get the current context from the message
        context = message.read_context()
        
        chat_history = message.get_chat_history()

        #re-render from the original content to ensure we have the latest template rendering
        fresh_content = TemplateHelper2.render_template(self.original_content, message.get_vars())

        # Send the prompt and get the response
        response = ask_with_context_and_spinner(fresh_content, context, chat_history)

        # Store the response in the specified output variable     
        message.set_var(self.output_var, response)

        # Also set the special __payload__ variable
        message.set_payload(self.content)

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