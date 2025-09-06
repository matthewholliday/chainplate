from ..send_prompt_element import SendPromptElement
from .mcp_prompts import MCP_GENERATE_PLAN_TEMPLATE, MCP_EXTRACT_TOOL_TEMPLATE, MCP_EXTRACT_PAYLOAD_TEMPLATE, MCP_EXTRACT_SERVICE_TEMPLATE
from .mcp_reserved_var_names import MCP_PLAN_VAR_NAME, MCP_TOOL_VAR_NAME, MCP_LOG_VAR_NAME, MCP_SERVICE_VAR_NAME, MCP_PAYLOAD_VAR_NAME

class MCPElementFactory:
    @staticmethod
    def create_extract_payload_element():
        return MCPElementFactory.create_element(MCP_PAYLOAD_VAR_NAME, MCP_EXTRACT_PAYLOAD_TEMPLATE)

    @staticmethod
    def create_extract_service_element():
        return MCPElementFactory.create_element(MCP_SERVICE_VAR_NAME, MCP_EXTRACT_SERVICE_TEMPLATE)

    @staticmethod
    def create_extract_tool_element():
        return MCPElementFactory.create_element(MCP_TOOL_VAR_NAME, MCP_EXTRACT_TOOL_TEMPLATE)

    @staticmethod
    def create_generate_plan_element():
        return MCPElementFactory.create_element(MCP_PLAN_VAR_NAME, MCP_GENERATE_PLAN_TEMPLATE)

    @staticmethod
    def create_element(output_var: str, content: str):
        return SendPromptElement(output_var=output_var, content=content)