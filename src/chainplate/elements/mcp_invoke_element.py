from .base_element import BaseElement
from ..services.mcp_service import MCPService
from ..message import Message

class MCPInvokeElement(BaseElement):
    def __init__(self, mcp_service, action, arguments):
        self.mcp_service = mcp_service
        self.action = action
        self.arguments = arguments

    async def enter(self, message: Message) -> Message:
        print("mih1")
        await MCPService().test_call_tool()
        print("mih2")
        return message

    def exit(self, message: Message) -> Message:
        return message