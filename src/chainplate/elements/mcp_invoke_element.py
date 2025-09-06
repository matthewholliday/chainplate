from .base_element import BaseElement
from ..services.mcp_service import MCPService
from ..message import Message

class MCPInvokeElement(BaseElement):
    def __init__(self, mcp_service, action, arguments):
        self.mcp_service = mcp_service
        self.action = action
        self.arguments = arguments

    async def enter(self, message: Message) -> Message:
        await MCPService().test_call_tool()
        return message

    def exit(self, message: Message) -> Message:
        return message