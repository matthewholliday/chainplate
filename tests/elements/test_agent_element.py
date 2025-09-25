import unittest
from unittest.mock import Mock, patch, MagicMock
import traceback

from src.chainplate.elements.agent_element import AgentElement
from src.chainplate.message import Message
from src.chainplate.execution_context import ExecutionContext
from src.chainplate.agent.agent_data import AgentData
from src.chainplate.agent.agent_environment import AgentEnvironment
from src.chainplate.exceptions import MissingAgentGoalsException, MissingMessageException


class TestAgentElement(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock execution context
        self.mock_execution_context = Mock(spec=ExecutionContext)
        self.mock_execution_context.execution_id = "test_execution_id"
        self.mock_execution_context.log_info = Mock()
        self.mock_execution_context.log_error = Mock()
        self.mock_execution_context.log_warning = Mock()
        
        # Create mock agent data and environment
        self.mock_agent_data = Mock(spec=AgentData)
        self.mock_agent_data.set_execution_id.return_value = self.mock_agent_data
        
        self.mock_agent_environment = Mock(spec=AgentEnvironment)
        self.mock_agent_environment.set_execution_id.return_value = self.mock_agent_environment
        
        # Create mock message
        self.mock_message = Mock(spec=Message)
        self.mock_message.read_context.return_value = "test context"
        self.mock_message.mcp_services = {"test_service": Mock()}
        self.mock_message.get_var.return_value = "test goals"
        
        # Create agent element with mocked dependencies
        self.agent_element = AgentElement(
            name="Test Agent",
            goals="test_goals_var",
            max_iterations=3,
            context=self.mock_execution_context,
            agent_data=self.mock_agent_data,
            agent_environment=self.mock_agent_environment
        )

    def test_initialization_default_parameters(self):
        """Test AgentElement initialization with default parameters."""
        # Create a fresh execution context for this test
        mock_context = Mock(spec=ExecutionContext)
        mock_context.execution_id = "default_test_id"
        mock_context.log_info = Mock()
        
        agent = AgentElement(context=mock_context)
        
        self.assertEqual(agent.name, "Unnamed Agent")
        self.assertEqual(agent.goals_var_name, "__agent_goals__")
        self.assertEqual(agent.max_iterations, 1)
        self.assertEqual(agent.execution_id, "default_test_id")
        self.assertIsNotNone(agent.llm_provider)
        self.assertIsNotNone(agent.action_engine)

    def test_initialization_custom_parameters(self):
        """Test AgentElement initialization with custom parameters."""
        self.assertEqual(self.agent_element.name, "Test Agent")
        self.assertEqual(self.agent_element.goals_var_name, "test_goals_var")
        self.assertEqual(self.agent_element.max_iterations, 3)
        self.assertEqual(self.agent_element.execution_id, "test_execution_id")
        
        # Verify that set_execution_id was called on dependencies
        self.mock_agent_data.set_execution_id.assert_called_once_with("test_execution_id")
        self.mock_agent_environment.set_execution_id.assert_called_once_with("test_execution_id")

    def test_get_tag(self):
        """Test the get_tag static method."""
        self.assertEqual(AgentElement.get_tag(), "agent")

    def test_get_label(self):
        """Test the get_label method."""
        label = self.agent_element.get_label()
        self.assertIsInstance(label, list)
        label_str = "".join(label)
        self.assertIn("Test Agent", label_str)
        self.assertIn("test_goals_var", label_str)
        self.assertIn("max_iterations=3", label_str)

    def test_enter_missing_message(self):
        """Test enter method with missing message raises exception."""
        with self.assertRaises(MissingMessageException) as context:
            self.agent_element.enter(None)
        
        self.assertIn("A valid Message object must be provided", str(context.exception))

    def test_enter_missing_goals(self):
        """Test enter method with missing goals raises exception."""
        self.mock_message.get_var.return_value = None
        
        with self.assertRaises(MissingAgentGoalsException) as context:
            self.agent_element.enter(self.mock_message)
        
        self.assertIn("was initialized without goals", str(context.exception))

    @patch.object(AgentElement, 'run_agent')
    def test_enter_success(self, mock_run_agent):
        """Test successful enter method execution."""
        mock_run_agent.return_value = self.mock_message
        
        result = self.agent_element.enter(self.mock_message)
        
        # Verify context and services were set
        self.assertEqual(self.agent_element.inherited_context, "test context")
        self.assertIn("test_service", self.agent_element.mcp_services)
        
        # Verify goals were saved
        self.mock_agent_data.save_goals.assert_called_once_with(goals="test goals")
        
        # Verify run_agent was called
        mock_run_agent.assert_called_once_with(self.mock_message)
        
        self.assertEqual(result, self.mock_message)

    def test_exit(self):
        """Test exit method simply returns the message."""
        result = self.agent_element.exit(self.mock_message)
        self.assertEqual(result, self.mock_message)

    @patch.object(AgentElement, 'generate_plan')
    @patch.object(AgentElement, 'run_agent_iteration')
    def test_run_agent_success_first_iteration(self, mock_run_iteration, mock_generate_plan):
        """Test run_agent completes successfully on first iteration."""
        mock_run_iteration.return_value = (True, self.mock_message)  # Task completed
        
        result = self.agent_element.run_agent(self.mock_message)
        
        mock_generate_plan.assert_called_once_with(message=self.mock_message)
        mock_run_iteration.assert_called_once_with(message=self.mock_message)
        self.mock_agent_environment.send_to_user.assert_called_with("iteration count: 1")
        self.assertEqual(result, self.mock_message)

    @patch.object(AgentElement, 'generate_plan')
    @patch.object(AgentElement, 'run_agent_iteration')
    def test_run_agent_max_iterations_reached(self, mock_run_iteration, mock_generate_plan):
        """Test run_agent reaches maximum iterations without completion."""
        mock_run_iteration.return_value = (False, self.mock_message)  # Task not completed
        
        result = self.agent_element.run_agent(self.mock_message)
        
        mock_generate_plan.assert_called_once_with(message=self.mock_message)
        self.assertEqual(mock_run_iteration.call_count, 3)  # max_iterations = 3
        self.mock_agent_environment.send_to_user.assert_called_with(
            "I reached the maximum number of iterations (3) without accomplishing the goals."
        )
        self.assertEqual(result, self.mock_message)

    @patch.object(AgentElement, 'get_next_action_text')
    @patch('src.chainplate.elements.agent_element.ActionEngine.perform_action')
    def test_run_agent_iteration_success(self, mock_perform_action, mock_get_action_text):
        """Test successful agent iteration."""
        mock_get_action_text.return_value = '{"action": "complete_task", "description": "test", "chain_of_thought": "test", "result": "done"}'
        mock_perform_action.return_value = True
        
        # Set mcp_services as it would be set in enter() method
        self.agent_element.mcp_services = {"test_service": Mock()}
        
        # Mock the action engine's convert method
        self.agent_element.action_engine.convert_action_text_to_object = Mock()
        self.agent_element.action_engine.convert_action_text_to_object.return_value = {
            "action": "complete_task",
            "description": "test",
            "chain_of_thought": "test",
            "result": "done"
        }
        
        is_complete, result_message = self.agent_element.run_agent_iteration(self.mock_message)
        
        self.assertTrue(is_complete)
        self.assertEqual(result_message, self.mock_message)
        self.mock_agent_environment.send_to_user.assert_called_with("Thinking about my next action...")
        mock_perform_action.assert_called_once()

    def test_create_generate_plan_prompt(self):
        """Test create_generate_plan_prompt method."""
        self.mock_agent_data.get_goals.return_value = "Test goal"
        
        prompt = self.agent_element.create_generate_plan_prompt(self.mock_message)
        
        self.assertIn("Test goal", prompt)
        self.assertIn("Generate a step-by-step plan", prompt)
        self.assertIn("intelligent agent", prompt)

    def test_create_generate_plan_prompt_exception(self):
        """Test create_generate_plan_prompt handles exceptions."""
        self.mock_agent_data.get_goals.side_effect = Exception("Test error")
        
        with self.assertRaises(Exception) as context:
            self.agent_element.create_generate_plan_prompt(self.mock_message)
        
        self.assertIn("An unexpected error occurred when attempting to generate the agent's plan", str(context.exception))

    @patch.object(AgentElement, 'send_llm_request')
    @patch.object(AgentElement, 'create_generate_plan_prompt')
    def test_generate_plan(self, mock_create_prompt, mock_send_llm):
        """Test generate_plan method."""
        mock_create_prompt.return_value = "test prompt"
        mock_send_llm.return_value = "test plan"
        
        self.agent_element.generate_plan(self.mock_message)
        
        mock_create_prompt.assert_called_once_with(self.mock_message)
        mock_send_llm.assert_called_once_with(prompt="test prompt", message=self.mock_message)
        self.mock_agent_data.save_plan.assert_called_once_with(plan="test plan")

    @patch.object(AgentElement, 'create_context_string')
    def test_generate_prompt(self, mock_create_context):
        """Test generate_prompt method."""
        mock_create_context.return_value = "test context"
        
        result = self.agent_element.generate_prompt(self.mock_message, "test prompt")
        
        expected = "test context\n\ntest prompt"
        self.assertEqual(result, expected)

    @patch.object(AgentElement, 'generate_prompt')
    def test_send_llm_request_success(self, mock_generate_prompt):
        """Test successful LLM request."""
        mock_generate_prompt.return_value = "full prompt"
        self.agent_element.llm_provider.ask_question = Mock(return_value="llm response")
        
        result = self.agent_element.send_llm_request("test prompt", self.mock_message)
        
        self.assertEqual(result, "llm response")
        self.agent_element.llm_provider.ask_question.assert_called_once()

    @patch.object(AgentElement, 'generate_prompt')
    def test_send_llm_request_empty_prompt_warning(self, mock_generate_prompt):
        """Test LLM request with empty prompt logs warning."""
        mock_generate_prompt.return_value = "full prompt"
        self.agent_element.llm_provider.ask_question = Mock(return_value="llm response")
        
        self.agent_element.send_llm_request("", self.mock_message)
        
        self.mock_execution_context.log_warning.assert_called_once_with(
            "No prompt was provided to the LLM request; using empty string as prompt."
        )

    @patch.object(AgentElement, 'generate_prompt')
    def test_send_llm_request_exception(self, mock_generate_prompt):
        """Test LLM request handles exceptions."""
        mock_generate_prompt.side_effect = Exception("Test error")
        
        with self.assertRaises(Exception) as context:
            self.agent_element.send_llm_request("test prompt", self.mock_message)
        
        self.assertIn("An unexpected error occurred when attempting to send a request to the LLM", str(context.exception))

    def test_debug_context_string_all_empty(self):
        """Test debug_context_string with all empty values."""
        self.agent_element.debug_context_string()
        
        # Verify appropriate log calls were made
        self.mock_execution_context.log_info.assert_any_call("Note: There is no inherited context from previous elements.")
        self.mock_execution_context.log_info.assert_any_call("Note: The working memory is currently empty.")
        self.mock_execution_context.log_error.assert_any_call("Note: The current goals are empty.")
        self.mock_execution_context.log_error.assert_any_call("Note: The current plan is empty.")
        self.mock_execution_context.log_warning.assert_any_call("Note: There are no services available.")
        self.mock_execution_context.log_warning.assert_any_call("Note: There are no tools available.")
        self.mock_execution_context.log_info.assert_any_call("Note: The chat history is currently empty.")

    def test_debug_context_string_with_values(self):
        """Test debug_context_string with non-empty values."""
        # Reset the mock to clear initialization calls
        self.mock_execution_context.reset_mock()
        
        self.agent_element.debug_context_string(
            chat_history="history",
            goals="goals",
            inherited_context="context",
            plan="plan",
            services="services",
            tools="tools",
            working_memory="memory"
        )
        
        # Verify no log calls were made since all values are present
        self.mock_execution_context.log_info.assert_not_called()
        self.mock_execution_context.log_error.assert_not_called()
        self.mock_execution_context.log_warning.assert_not_called()

    def test_create_context_string_success(self):
        """Test successful context string creation."""
        # Mock all the agent_data methods
        self.mock_agent_data.get_chat_history_summary.return_value = "chat history"
        self.mock_agent_data.get_goals.return_value = "goals"
        self.mock_agent_data.get_plan.return_value = "plan"
        self.mock_agent_data.get_services.return_value = "services"
        self.mock_agent_data.get_tools.return_value = "tools"
        self.mock_agent_data.get_working_memory.return_value = "memory"
        
        self.agent_element.inherited_context = "inherited"
        
        result = self.agent_element.create_context_string(self.mock_message)
        
        self.assertIn("chat history", result)
        self.assertIn("goals", result)
        self.assertIn("plan", result)
        self.assertIn("services", result)
        self.assertIn("tools", result)
        self.assertIn("memory", result)
        self.assertIn("inherited", result)

    def test_create_context_string_exception(self):
        """Test create_context_string handles exceptions."""
        self.mock_agent_data.get_chat_history_summary.side_effect = Exception("Test error")
        
        with self.assertRaises(Exception) as context:
            self.agent_element.create_context_string(self.mock_message)
        
        self.assertIn("An unexpected error occurred when attempting to create the context string", str(context.exception))

    @patch.object(AgentElement, 'send_llm_request')
    def test_get_next_action_text(self, mock_send_llm):
        """Test get_next_action_text method."""
        mock_send_llm.return_value = "action response"
        
        # Reset mock to clear initialization calls
        self.mock_execution_context.reset_mock()
        
        result = self.agent_element.get_next_action_text(self.mock_message)
        
        self.assertEqual(result, "action response")
        mock_send_llm.assert_called_once()
        self.mock_execution_context.log_info.assert_called_once()

    def test_initialization_logs_proper_messages(self):
        """Test that initialization logs the expected messages."""
        # Verify execution context logging
        expected_calls = [
            unittest.mock.call("Initializing AgentElement with execution_id: test_execution_id"),
            unittest.mock.call("Agent goals variable name set to: test_goals_var")
        ]
        self.mock_execution_context.log_info.assert_has_calls(expected_calls)

    def test_agent_element_attributes(self):
        """Test that all expected attributes are set correctly."""
        self.assertEqual(self.agent_element.next_action_text, "No action has been determined yet.")
        self.assertEqual(self.agent_element.inherited_context, "")
        self.assertIsNotNone(self.agent_element.llm_provider)
        self.assertIsNotNone(self.agent_element.action_engine)
        self.assertEqual(self.agent_element.execution_context, self.mock_execution_context)


if __name__ == '__main__':
    unittest.main()
