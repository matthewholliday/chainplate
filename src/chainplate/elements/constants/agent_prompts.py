ACTION_PLAN_SELCTION_PROMPT = """
Provide a valid output based on the context already provided to you.

There are three valid JSON structures that you can output depending on the appropriate course of action for the NEXT step in the plan. Please ensure that your output strictly adheres to one of the following structures:

1. MCP Tool Call - If you determine that a tool call is necessary to achieve the goals, output the following JSON structure:

{
  "chain_of_thought" : <your_explanation_of_why_this_tool_call_is_necessary_and_consistent_with_the_plan>,
  "description" : <a_brief_description_of_the_tool_call_and_its_purpose>,
  "action": "mcp_tool_call",
  "service_name": "<name_of_the_mcp_service>",
    "tool_name": "<name_of_the_tool_to_call>",
    "arguments": {
      "<argument_name>": "<argument_value>",
        "...": "..."
    }
}

Valid services are the names of the corresponding platform, e.g. "notion", "jira", "slack", etc. Valid tool names are the names of the tools that are available in the MCP service.

2. Ask Question To User - If you need more information from the user to proceed, output the following JSON structure:
{
  "chain_of_thought" : <your_explanation_of_why_this_question_is_necessary_and_consistent_with_the_plan>,
  "description" : <a_brief_description_of_the_question_and_its_purpose>,
  "action": "ask_question_to_user",
  "question": "<your_question_here>"
}

3. Modify Plan - If you need to modify the existing plan based on new information or insights, output the following JSON structure:
{
  "chain_of_thought" : <your_explanation_of_why_this_plan_modification_is_necessary_and_consistent_with_the_goals>,
  "description" : <a_brief_description_of_the_plan_modification_and_its_purpose>,
  "action": "modify_plan",
  "new_plan": "<your_modified_plan_here>"
}

Assumptions you should make:
-The user's intention is for you to perform as much of the work as possible without needing to ask for additional information unless absolutely necessary.
-You should only ask questions when you are unable to proceed with the current information and context provided to you.
-Authentication and authorization for MCP tool calls are handled outside of your scope, so you can assume that any tool call you make will be authorized.
-Do not ask the user if they want you to provide step-by-step manual UI instructions. Assume that you should carry out the actions yourself unless you are explicitly instructed otherwise.

"""

ACTION_PLAN_SELCTION_SYSTEM = """
You are an intelligent agent tasked with selecting the appropriate action based on the provided context and goals. Your output must strictly adhere to one of the three valid JSON structures outlined in the prompt. Ensure that there is absolutely no other text or information included in your output beyond the specified JSON structure.
"""