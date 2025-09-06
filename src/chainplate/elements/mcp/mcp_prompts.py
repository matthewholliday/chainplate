MCP_GENERATE_PLAN_TEMPLATE = """
You are an MCP client orchestrator. Your job is to analyze the current situation and formulate a clear, step-by-step plan for how to proceed. Here is contextual information about what has happened so far:

Available Tools:
{{ __mcp_available_tools__}}

Chat History:
{{ __mcp_chat_history__ }}

What has occurred in the current MCP session:
{{ __mcp_logs__ }}

"""

MCP_EXTRACT_TOOL_TEMPLATE = """
You are an assistant. You will be given some instructions. Your only task is to determine which MCP tool those instructions say should be called. Output only the exact name of that MCP tool, with no explanation, formatting, or extra text. If no tool is specified, output nothing. 

Here are the instructions:

 {{ input_text }}
"""

MCP_EXTRACT_PAYLOAD_TEMPLATE = """
You are an assistant. You will be given some instructions. Your only task is to determine which MCP payload those instructions say should be called. Output only the exact name of that MCP tool, with no explanation, formatting, or extra text. If no tool is specified, output nothing. 

Here are the instructions:

 {{ input_text }}
"""

MCP_EXTRACT_SERVICE_TEMPLATE = """
You are an assistant. You will be given some instructions. Your only task is to determine which MCP service those instructions say should be called. Output only the exact name of that MCP tool, with no explanation, formatting, or extra text. If no tool is specified, output nothing. 

Here are the instructions:

 {{ input_text }}
"""