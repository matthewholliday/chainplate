from ..message import Message
from .base_element import BaseElement
from ..execution_context import ExecutionContext
from ..execution_context import ExecutionContext
from ..services.logging.logging_service import LoggingService
from ..services.data.data_service import DataService
from ..services.ux.async_ux_service import AsyncUserExperienceService
import traceback

class GetUserInputElement(BaseElement):
    def __init__(self, output_var, content, context: ExecutionContext = None):
        super().__init__(context=context)
        LoggingService.log_info("Initializing GetUserInputElement")
        #TODO: come up with better defaults...
        self.output_var = "unnamed" if output_var is None else output_var
        self.content = content
        self.context = context
        self.data_service = DataService()
        exec_id = getattr(context, 'execution_id', None)
        # Fallback to 0 for test contexts without execution tracking
        self.ux_service = AsyncUserExperienceService(execution_id=exec_id or 0, data_service=self.data_service)


    def enter(self , message: Message) -> Message:
        LoggingService.log_info(f"Entering GetUserInputElement with output_var: {self.output_var} and content: {self.content}")
        try:
            self.content = self.apply_template(self.content, message)

            message = message.set_var(self.output_var, self.content)

            user_input = self.ux_service.get_user_input(prompt=self.content)
            LoggingService.log_info(f"User input received: {user_input}")
            
            message = message.set_var(self.output_var, user_input)
        except Exception as e:
            LoggingService.log_error(f"Error in GetUserInputElement: {e} {traceback.format_tb(e.__traceback__)}")
            message = message.set_var(self.output_var, "")

        return message

    def exit(self, message: Message) -> Message:
        return message
    
    def get_label(self) -> str:
        return f"GetUserInputElement(output_var={self.output_var}, content={self.content})"
    
    @staticmethod
    def get_tag() -> str:
        return "get-user-input"