from ..services.mcp_service import MCPService
from .base_element import BaseElement
from ..message import Message
import asyncio

class MCPListToolsElement(BaseElement):
    def __init__(self, output_var: str = "__mcp_available_tools__", mcp_service: str = "notion"):
        super().__init__()
        self.output_var = output_var
        self.service = mcp_service

    async def enter(self, message) -> Message:
        service = MCPService()
        tools_list = await service.list_tools()
        message.set_var(self.output_var, tools_list)
        return message

    def exit(self, message):
        return message