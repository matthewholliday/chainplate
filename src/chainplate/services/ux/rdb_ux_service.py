from .ux_service import UXService
from ..data.database.rdb_service import RDBService
from ...config import USER_DISPLAY_NAME, SYSTEM_DISPLAY_NAME

class RelationalDatabaseUXService(UXService):
    def __init__(self, conversation_id: str):
        self.connection = RDBService().create_connection()
        self.conversation_id = conversation_id

    def get_input_from_user(self, prompt):
        return input(prompt)
    
    def show_output_to_user(self, output):
        print(output)

    def show_output_to_user(self, output) -> None:
        RDBService().add_message(self.connection, self.conversation_id, "assistant", output)

    def poll_db_for_input(self, latest_id: str) -> str:
        checked_id = latest_id
        message_record = {}
        while latest_id == checked_id:
            message_record = RDBService().get_newest_message(self.connection, self.conversation_id)
            checked_id = message_record[0] if message_record else None
        return message_record.content if message_record else "No content found in message record."