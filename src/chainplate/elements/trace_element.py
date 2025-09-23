from .base_element import BaseElement
from ..message import Message
from ..services.data.data_service import DataService
from ..execution_context import ExecutionContext

class TraceElement(BaseElement):
    def __init__(self, execution_id: str = None, content: str = "", is_blocking: bool = False, context: ExecutionContext = None):
        super().__init__(context=context)
        self.execution_id = execution_id
        self.content = content
        self.is_blocking = is_blocking
        self.context = context
        self.data_service = DataService()
    
    def enter(self, message: Message) -> Message:
        self.create_execution_step()
        return message

    def exit(self, message):
        return message

    def create_execution_step(self):
        try:
            data_service = DataService()
            data_service.add_execution_step(
                execution_id=self.context.execution_id,
                content=self.content,
                role="TRACE",
                channel=3,
                requires_input=self.is_blocking,
                response_to=None,
            )
        except Exception as e:
            print(f"Error creating execution step in TraceElement: {e}")
            raise e
        finally:
            data_service.close()

    def get_label(self) -> str:
        return f"TraceElement(execution_id={self.execution_id}, content={self.content}, is_blocking={self.is_blocking})"
    
    @staticmethod
    def get_tag():
        return "trace"