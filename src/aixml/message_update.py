from .message import Message
from .helpers.logging_helper import LoggingHelper

class MessageUpdate:
    def __init__(self, message: Message, payload: any ={}, sucess: bool=True):
        self.message = message
        self.sucess = sucess
        self.error = None
        self.payload = payload

    def set_error(self,error) -> "MessageUpdate":
        message = f"Error: {str(error)}"
        self.error = error
        self.message = LoggingHelper().log_message(text=message, message=self.message)
        self.sucess = False
        return self
    
    def set_payload(self,payload) -> "MessageUpdate":
        self.payload = payload
        return self
    
    def get_error(self) -> any:
        return self.error
    
    def get_payload(self) -> any:
        return self.payload
    
    def get_success(self) -> bool:
        return self.sucess
    
    def get_message(self) -> Message:
        return self.message