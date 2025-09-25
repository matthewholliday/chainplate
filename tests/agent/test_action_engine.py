import unittest
import json
from unittest.mock import Mock, patch, MagicMock

from src.chainplate.agent.action_engine import (
    ActionEngine,
    MCPToolCallAction,
    AskQuestionToUserAction,
    ModifyPlanAction,
    MarkTaskAsCompleteAction
)


class TestActionEngine(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.action_engine = ActionEngine()
        self.mock_execution_context = Mock()
        self.mock_agent_environment = Mock()
        self.mock_agent_data = Mock()
        self.mock_mcp_services = {}
        
        # Sample valid action objects for testing
        self.valid_mcp_action = {
            "action": "mcp_tool_call",
            "chain_of_thought": "I need to call a tool",
            "description": "Testing MCP tool call",
            "service_name": "test_service",
            "tool_name": "test_tool",
            "arguments": {"param": "value"}
        }
        
        self.valid_ask_question_action = {
            "action": "ask_question_to_user",
            "chain_of_thought": "I need to ask the user",
            "description": "Testing user question",
            "question": "What is your name?"
        }
        
        self.valid_modify_plan_action = {
            "action": "modify_plan",
            "chain_of_thought": "I need to modify the plan",
            "description": "Testing plan modification",
            "new_plan": "Updated plan"
        }
        
        self.valid_complete_task_action = {
            "action": "complete_task",
            "chain_of_thought": "Task is done",
            "description": "Testing task completion",
            "result": "Task completed successfully"
        }

    def test_convert_action_text_to_object_valid_json(self):
        """Test converting valid JSON text to action object."""
        action_text = json.dumps(self.valid_mcp_action)
        result = self.action_engine.convert_action_text_to_object(action_text)
        self.assertEqual(result, self.valid_mcp_action)

    def test_convert_action_text_to_object_invalid_json(self):
        """Test converting invalid JSON text raises exception."""
        invalid_json = "{ invalid json }"
        
        with self.assertRaises(Exception) as context:
            self.action_engine.convert_action_text_to_object(invalid_json, self.mock_execution_context)
        
        self.assertIn("An unexpected error occurred while parsing MCP action text to JSON", str(context.exception))
        self.mock_execution_context.log_error.assert_called_once()

    def test_convert_action_text_to_object_invalid_json_no_context(self):
        """Test converting invalid JSON without execution context."""
        invalid_json = "{ invalid json }"
        
        with self.assertRaises(Exception):
            self.action_engine.convert_action_text_to_object(invalid_json)

    def test_validate_action_object_valid_mcp_action(self):
        """Test validation of valid MCP tool call action."""
        self.assertTrue(ActionEngine.validate_action_object(self.valid_mcp_action))

    def test_validate_action_object_valid_ask_question_action(self):
        """Test validation of valid ask question action."""
        self.assertTrue(ActionEngine.validate_action_object(self.valid_ask_question_action))

    def test_validate_action_object_valid_modify_plan_action(self):
        """Test validation of valid modify plan action."""
        self.assertTrue(ActionEngine.validate_action_object(self.valid_modify_plan_action))

    def test_validate_action_object_valid_complete_task_action(self):
        """Test validation of valid complete task action."""
        self.assertTrue(ActionEngine.validate_action_object(self.valid_complete_task_action))

    def test_validate_action_object_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        invalid_action = {"action": "mcp_tool_call"}  # Missing required fields
        self.assertFalse(ActionEngine.validate_action_object(invalid_action))

    def test_validate_action_object_missing_action_specific_fields(self):
        """Test validation fails when action-specific fields are missing."""
        invalid_mcp_action = {
            "action": "mcp_tool_call",
            "chain_of_thought": "test",
            "description": "test"
            # Missing service_name, tool_name, arguments
        }
        self.assertFalse(ActionEngine.validate_action_object(invalid_mcp_action))

    def test_validate_action_object_unknown_action(self):
        """Test validation fails for unknown action types."""
        unknown_action = {
            "action": "unknown_action",
            "chain_of_thought": "test",
            "description": "test"
        }
        self.assertFalse(ActionEngine.validate_action_object(unknown_action))

    def test_validate_action_object_no_action(self):
        """Test validation fails when action field is missing."""
        no_action = {
            "chain_of_thought": "test",
            "description": "test"
        }
        self.assertFalse(ActionEngine.validate_action_object(no_action))

    def test_get_mcp_service_valid_service(self):
        """Test getting a valid MCP service."""
        mock_service = Mock()
        mcp_services = {"test_service": mock_service}
        
        result = ActionEngine.get_mcp_service("test_service", mcp_services)
        self.assertEqual(result, mock_service)

    def test_get_mcp_service_case_insensitive(self):
        """Test getting MCP service is case insensitive."""
        mock_service = Mock()
        mcp_services = {"test_service": mock_service}
        
        result = ActionEngine.get_mcp_service("TEST_SERVICE", mcp_services)
        self.assertEqual(result, mock_service)

    def test_get_mcp_service_not_found(self):
        """Test getting non-existent MCP service raises ValueError."""
        mcp_services = {"other_service": Mock()}
        
        with self.assertRaises(ValueError) as context:
            ActionEngine.get_mcp_service("test_service", mcp_services)
        
        self.assertIn("Requested MCP service 'test_service' is not available", str(context.exception))

    @patch.object(ActionEngine, 'call_mcp_tool')
    def test_perform_action_mcp_tool_call(self, mock_call_mcp_tool):
        """Test performing MCP tool call action."""
        is_complete = ActionEngine.perform_action(
            self.valid_mcp_action,
            self.mock_execution_context,
            self.mock_agent_environment,
            self.mock_agent_data,
            self.mock_mcp_services
        )
        
        self.assertFalse(is_complete)
        mock_call_mcp_tool.assert_called_once()

    @patch.object(ActionEngine, 'ask_user_question')
    def test_perform_action_ask_question_to_user(self, mock_ask_user_question):
        """Test performing ask question to user action."""
        mock_ask_user_question.return_value = "User response"
        
        is_complete = ActionEngine.perform_action(
            self.valid_ask_question_action,
            self.mock_execution_context,
            self.mock_agent_environment,
            self.mock_agent_data,
            self.mock_mcp_services
        )
        
        self.assertFalse(is_complete)
        mock_ask_user_question.assert_called_once()

    @patch.object(ActionEngine, 'modify_plan')
    def test_perform_action_modify_plan(self, mock_modify_plan):
        """Test performing modify plan action."""
        is_complete = ActionEngine.perform_action(
            self.valid_modify_plan_action,
            self.mock_execution_context,
            self.mock_agent_environment,
            self.mock_agent_data,
            self.mock_mcp_services
        )
        
        self.assertFalse(is_complete)
        mock_modify_plan.assert_called_once()

    @patch.object(ActionEngine, 'mark_task_as_complete')
    def test_perform_action_complete_task(self, mock_mark_task_as_complete):
        """Test performing complete task action."""
        is_complete = ActionEngine.perform_action(
            self.valid_complete_task_action,
            self.mock_execution_context,
            self.mock_agent_environment,
            self.mock_agent_data,
            self.mock_mcp_services
        )
        
        self.assertTrue(is_complete)
        mock_mark_task_as_complete.assert_called_once()

    def test_perform_action_invalid_action_object(self):
        """Test performing action with invalid action object raises ValueError."""
        invalid_action = {"invalid": "action"}
        
        with self.assertRaises(ValueError) as context:
            ActionEngine.perform_action(
                invalid_action,
                self.mock_execution_context,
                self.mock_agent_environment,
                self.mock_agent_data,
                self.mock_mcp_services
            )
        
        self.assertIn("Invalid action object received", str(context.exception))
        self.mock_execution_context.log_error.assert_called_once()

    def test_mark_task_as_complete(self):
        """Test marking task as complete."""
        action = MarkTaskAsCompleteAction(
            chain_of_thought="Task is done",
            description="Test completion",
            result="Success"
        )
        
        ActionEngine.mark_task_as_complete(
            action,
            self.mock_agent_environment,
            self.mock_agent_data
        )
        
        self.mock_agent_environment.send_to_user.assert_called_once()
        self.mock_agent_data.add_memory.assert_called_once()

    def test_modify_plan(self):
        """Test modifying plan."""
        action = ModifyPlanAction(
            chain_of_thought="Need to change plan",
            description="Test modification",
            new_plan="New plan content"
        )
        
        ActionEngine.modify_plan(
            action,
            self.mock_agent_environment,
            self.mock_agent_data
        )
        
        self.mock_agent_environment.send_to_user.assert_called_once()
        self.mock_agent_data.add_memory.assert_called_once()

    def test_ask_user_question(self):
        """Test asking user a question."""
        action = AskQuestionToUserAction(
            chain_of_thought="Need user input",
            description="Test question",
            question="What is your favorite color?"
        )
        
        self.mock_agent_environment.get_user_input.return_value = "Blue"
        
        result = ActionEngine.ask_user_question(
            action,
            self.mock_agent_environment,
            self.mock_agent_data
        )
        
        self.assertEqual(result, "Blue")
        self.mock_agent_environment.get_user_input.assert_called_once_with(prompt="What is your favorite color?")
        self.mock_agent_data.add_memory.assert_called_once()

    @patch.object(ActionEngine, 'get_mcp_service')
    def test_call_mcp_tool_success(self, mock_get_mcp_service):
        """Test successful MCP tool call."""
        mock_service = Mock()
        mock_service.call_tool.return_value = "Tool result"
        mock_get_mcp_service.return_value = mock_service
        
        action = MCPToolCallAction(
            arguments={"param": "value"},
            chain_of_thought="Calling tool",
            description="Test tool call",
            service_name="test_service",
            tool_name="test_tool"
        )
        
        ActionEngine.call_mcp_tool(
            action,
            self.mock_agent_environment,
            self.mock_agent_data,
            self.mock_mcp_services
        )
        
        mock_service.call_tool.assert_called_once_with(tool_name="test_tool", arguments={"param": "value"})
        self.mock_agent_environment.send_to_user.assert_called()
        self.mock_agent_data.add_memory.assert_called_once()

    @patch.object(ActionEngine, 'get_mcp_service')
    def test_call_mcp_tool_failure(self, mock_get_mcp_service):
        """Test MCP tool call failure."""
        mock_service = Mock()
        mock_service.call_tool.side_effect = Exception("Tool error")
        mock_get_mcp_service.return_value = mock_service
        
        action = MCPToolCallAction(
            arguments={"param": "value"},
            chain_of_thought="Calling tool",
            description="Test tool call",
            service_name="test_service",
            tool_name="test_tool"
        )
        
        with self.assertRaises(Exception) as context:
            ActionEngine.call_mcp_tool(
                action,
                self.mock_agent_environment,
                self.mock_agent_data,
                self.mock_mcp_services
            )
        
        self.assertIn("An error occurred while calling MCP tool", str(context.exception))
        self.mock_agent_environment.send_to_user.assert_called()

    def test_create_tool_call_memory_string(self):
        """Test creating tool call memory string."""
        result = ActionEngine.create_tool_call_memory_string(
            description="Test description",
            chain_of_thought="Test thought",
            tool_name="test_tool",
            service_name="test_service",
            arguments={"param": "value"},
            result="Tool result"
        )
        
        self.assertIsInstance(result, str)
        self.assertIn("Test description", result)
        self.assertIn("Test thought", result)
        self.assertIn("test_tool", result)
        self.assertIn("test_service", result)
        self.assertIn("Tool result", result)


if __name__ == '__main__':
    unittest.main()
