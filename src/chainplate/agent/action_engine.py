from ..message import Message
import dataclasses
import json
import traceback

@dataclasses.dataclass
class MCPToolCallAction:
    arguments: dict
    chain_of_thought: str
    description: str
    service_name: str
    tool_name: str

@dataclasses.dataclass
class AskQuestionToUserAction:
    chain_of_thought: str
    description: str
    question: str

@dataclasses.dataclass
class ModifyPlanAction:
    chain_of_thought: str
    description: str
    new_plan: str

@dataclasses.dataclass
class MarkTaskAsCompleteAction:
    chain_of_thought: str
    description: str
    result: str



class ActionEngine:
    def convert_action_text_to_object(self, action_text: str, execution_context=None):
        action_object = {}

        try:
            action_object = json.loads(action_text)
        except json.JSONDecodeError as e:
            error_message = f"An unexpected error occurred while parsing MCP action text to JSON. Here is the action text that caused the error:\n\n{action_text}\n\nError details: {e}\n{traceback.format_exc()}"
            if execution_context:
                execution_context.log_error(error_message)
            raise Exception(error_message) #TODO: decide if we want to raise here or just log and continue with empty action_object
        return action_object

    @staticmethod
    def perform_action(action_object: dict = {}, execution_context = None, agent_environment=None, agent_data=None, mcp_services=None) -> bool:
        action_type = ""
        chain_of_thought = ""
        description = ""

        task_is_complete = False

        if not ActionEngine.validate_action_object(action_object):
            error_message = f"Invalid action object received: {action_object}"
            execution_context.log_error(error_message)
            raise ValueError(error_message)

        action_type = action_object.get("action", "unknown")
        description = action_object.get("description", "")         
        chain_of_thought = action_object.get("chain_of_thought", "")

        task_is_complete = False

        if(action_type == "mcp_tool_call"):
            arguments = action_object.get("arguments", {})
            service_name = action_object.get("service_name", "ERROR_MISSING_SERVICE_NAME")
            tool_name = action_object.get("tool_name", "ERROR_MISSING_TOOL_NAME")

            mcp_tool_call_action = MCPToolCallAction(
                arguments=arguments,
                chain_of_thought=chain_of_thought,
                description=description,
                service_name=service_name,
                tool_name=tool_name
            )

            ActionEngine.call_mcp_tool(
                mcp_tool_call_action=mcp_tool_call_action,
                agent_environment=agent_environment,
                agent_data=agent_data,
                mcp_services=mcp_services
            )

        elif(action_type == "ask_question_to_user"):
            question = action_object.get("question", "ERROR_MISSING_QUESTION")
            ask_user_action = AskQuestionToUserAction(
                chain_of_thought=chain_of_thought,
                description=description,
                question=question
            )
            ActionEngine.ask_user_question(ask_user_action, agent_environment, agent_data)
        elif(action_type == "modify_plan"):
            new_plan = action_object.get("new_plan", "ERROR_MISSING_NEW_PLAN")

            modify_plan_action = ModifyPlanAction(
                chain_of_thought=chain_of_thought,
                description=description,
                new_plan=new_plan
            )
            ActionEngine.modify_plan(modify_plan_action, agent_environment, agent_data)
        elif(action_type == "complete_task"):
            result = action_object.get("result", "ERROR_MISSING_RESULT")
            
            mark_task_as_complete_action = MarkTaskAsCompleteAction(
                chain_of_thought=chain_of_thought,
                description=description,
                result=result
            )

            ActionEngine.mark_task_as_complete(
                mark_task_as_complete_action=mark_task_as_complete_action,
                agent_environment=agent_environment,
                agent_data=agent_data
            )
            task_is_complete = True
            
        return task_is_complete

    # Helper methods...
    
    @staticmethod
    def get_mcp_service(service_name: str = "", mcp_services = {}):
        lowercase_service_name = service_name.lower() # MCP service names are case-insensitive, so we standardize to lowercase
        if lowercase_service_name not in mcp_services:
            error_message = f"Requested MCP service '{service_name}' is not available. Available services: {list(mcp_services.keys())}"
            raise ValueError(error_message)
        return mcp_services[lowercase_service_name]


    # Action implementation methods...

    @staticmethod
    def mark_task_as_complete(mark_task_as_complete_action: MarkTaskAsCompleteAction = None, agent_environment = None, agent_data = None) -> None:
        completion_message = f"Task completed. Result: {mark_task_as_complete_action.result}"
        agent_environment.send_to_user(completion_message)
        agent_data.add_memory(entry=f"Agent completed the task: {mark_task_as_complete_action.description}\n\nAgent's chain of thought before completing the task: {mark_task_as_complete_action.chain_of_thought}\n\n{completion_message}")
    
    @staticmethod
    def modify_plan(modify_plan_action: ModifyPlanAction = None, agent_environment = None, agent_data = None) -> None:
        message_content = f"I am modifying my plan. New plan:\n\n{modify_plan_action.new_plan}"
        agent_environment.send_to_user(message_content)
        agent_data.add_memory(entry=f"Agent modified its plan to: {modify_plan_action.new_plan}\n\nAgent was trying to: {modify_plan_action.description}\n\nAgent's chain of thought before modifying the plan: {modify_plan_action.chain_of_thought}")

    @staticmethod
    def ask_user_question(ask_user_action: AskQuestionToUserAction = None, agent_environment = None, agent_data = None) -> str:
        user_response = agent_environment.get_user_input(prompt=ask_user_action.question)
        agent_data.add_memory(entry=f"Agent asked the user a question: {ask_user_action.question}\n\nAgent was trying to: {ask_user_action.description}\n\nAgent's chain of thought before asking the question: {ask_user_action.chain_of_thought}\n\nUser's response: {user_response}")
        return user_response
    
    @staticmethod
    def call_mcp_tool(mcp_tool_call_action: MCPToolCallAction, agent_environment = None, agent_data = None, mcp_services = {}) -> None:
        # Inform the user we're calling a tool
        agent_environment.send_to_user(f"I'm calling MCP tool '{mcp_tool_call_action.tool_name}' from service '{mcp_tool_call_action.service_name}'.") 

        # MCP service names are case-insensitive, so we standardize to lowercase
        mcp_service = ActionEngine.get_mcp_service(service_name=mcp_tool_call_action.service_name, mcp_services=mcp_services)

        try:
            result = mcp_service.call_tool(tool_name=mcp_tool_call_action.tool_name, arguments=mcp_tool_call_action.arguments)
        except Exception as e:
            error_message = f"An error occurred while calling MCP tool '{mcp_tool_call_action.tool_name}' from service '{mcp_tool_call_action.service_name}' with arguments {mcp_tool_call_action.arguments}. Error details: {e}\n{traceback.format_exc()}"
            agent_environment.send_to_user(error_message)
            raise Exception(error_message)

        agent_data.add_memory(entry=ActionEngine.create_tool_call_memory_string(
            mcp_tool_call_action.description,
            mcp_tool_call_action.chain_of_thought,
            mcp_tool_call_action.tool_name,
            mcp_tool_call_action.service_name,
            mcp_tool_call_action.arguments,
            result
        ))
        result_message = f"I received a result from the tool call: {result}"
        agent_environment.send_to_user(result_message)

    @staticmethod
    def create_tool_call_memory_string(description: str = "", chain_of_thought: str = "", tool_name: str = "", service_name: str = "", arguments: any = None, result = None) -> str:
        tool_call_string = f"Agent called MCP tool:\n\n  TOOL: '{tool_name}'\n\n  SERVICE: '{service_name}'\n\n  ARGUMENTS: {arguments}\n\n  RESPONSE: \n{result}"
        agent_reasoning = f"Agent was trying to: {description}\n\nAgent's chain of thought before calling the tool: {chain_of_thought}"
        memory_string = f"{agent_reasoning}\n\n{tool_call_string}"
        return memory_string

    @staticmethod
    def validate_action_object(action_object: dict) -> bool:
        required_fields = ["action", "chain_of_thought", "description"]
        action = action_object.get("action", None)
        if not action:
            return False
        for field in required_fields:
            if field not in action_object:
                return False
        if action == "mcp_tool_call":
            tool_required_fields = ["service_name", "tool_name", "arguments"]
            for field in tool_required_fields:
                if field not in action_object:
                    return False
        elif action == "ask_question_to_user":
            if "question" not in action_object:
                return False
        elif action == "modify_plan":
            if "new_plan" not in action_object:
                return False
        elif action == "complete_task":
            if "result" not in action_object:
                return False
        else:
            return False
        return True
