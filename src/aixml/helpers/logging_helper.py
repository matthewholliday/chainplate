from .template_helper import TemplateHelper
from ..message import Message

class LoggingHelper:
    @staticmethod
    def log(message: str):
        print(message)

    def get_formatted_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log_message(self, text: str, message: Message) -> Message:
        try:
            updated_text: str = TemplateHelper.render_template(text, message.get_vars())
            header: str = self.get_header(message)
            footer: str = self.get_footer()
            full_log_entry = f"{header}\n{updated_text}\n{footer}"
            message.log(full_log_entry)
        except Exception as e:
            message.log(f"A logging error occurred: {e}")
        return message
    
    def get_header(self, text, message: Message) -> str:
        timestamp = message.get_formatted_timestamp()
        formatted_text = f"[{timestamp}]"
        formatted_text += "\n" + text

    def get_footer(self) -> str:
        return "===============END LOG ENTRY================\n\n"    

    