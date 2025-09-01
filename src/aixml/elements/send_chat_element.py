from ..message import Message
from .ai_base_element import AiBaseElement

class SendChatElement(AiBaseElement):
    def __init__(self, name, output_var, content, conversation_history=[]):
        super().__init__(name, output_var)
        self.content = content
        self.transformed_content = content
        self.conversation_history = conversation_history

    def enter(self , message: Message) -> Message:
        message = self.try_transform_content(message)
        self.transformed_content = message.ask_llm(self.transformed_content)
        new_entry = SendChatElement.create_conversation_entry("user", self.transformed_content)
        message.conversation_history.append(new_entry)
        message = self.try_set_variable(message)
        return message

    def exit(self, message: Message) -> Message:
        return message

    def should_enter(self, message: Message) -> bool:
        return True
    
    def increment_iteration(self, message):
        return message

    def should_exit(self, message: Message) -> tuple[bool, Message]:
        return (True, message)
    
    @staticmethod
    def create_conversation_entry(role: str, content: str) -> dict:
        return {"role": role, "content": content}