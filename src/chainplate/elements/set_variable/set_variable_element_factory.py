from ..mcp.mcp_reserved_var_names import MCP_PLAN_VAR_NAME, MCP_TOOL_VAR_NAME, MCP_LOG_VAR_NAME, MCP_SERVICE_VAR_NAME, MCP_PAYLOAD_VAR_NAME
from ..set_variable_element import SetVariableElement

class SetVariableElementFactory:
    @staticmethod
    def create_set_mcp_plan_element(content: str):
        return SetVariableElementFactory.create_element(MCP_PLAN_VAR_NAME, content)
    
    @staticmethod
    def create_set_mcp_tool_element(content: str):
        return SetVariableElementFactory.create_element(MCP_TOOL_VAR_NAME, content)
    
    @staticmethod
    def create_set_mcp_log_element(content: str):
        return SetVariableElementFactory.create_element(MCP_LOG_VAR_NAME, content)
    
    @staticmethod
    def create_set_mcp_service_element(content: str):
        return SetVariableElementFactory.create_element(MCP_SERVICE_VAR_NAME, content)
    
    @staticmethod
    def create_set_mcp_payload_element(content: str):
        return SetVariableElementFactory.create_element(MCP_PAYLOAD_VAR_NAME, content)

    @staticmethod
    def create_element(output_var: str, content: str):
        return SetVariableElement(output_var=output_var, content=content)