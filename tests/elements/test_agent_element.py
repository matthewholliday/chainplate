import unittest
from unittest.mock import MagicMock, patch
from src.chainplate.message import Message
from src.chainplate.elements.agent_element import AgentElement
from src.chainplate.agent.agent_data import AgentData

class TestAgentElement(unittest.TestCase):
    def test_constructor_defaults(self):
        agent = AgentElement()
        self.assertEqual(agent.name, "Unnamed Agent")
        self.assertEqual(agent.goals_var_name, "default_goal_var")
        self.assertEqual(agent.payload_var_name, "__payload__")
        self.assertEqual(agent.max_iterations, 1)
        self.assertEqual(agent.next_action_text, "No action has been determined yet.")
        self.assertIsNotNone(agent.agent_data)
        self.assertIsNotNone(agent.agent_environment)
        self.assertEqual(agent.inherited_context, "")
        self.assertEqual(agent.execution_id, "")
    
    def test_constructor_custom_values(self):
        agent = AgentElement(
            name="ResearchAgent",
            goals="goal_var",
            output_var="result_var",
            max_iterations=5,
            execution_id="exec-123"
        )
        self.assertEqual(agent.name, "ResearchAgent")
        self.assertEqual(agent.goals_var_name, "goal_var")
        self.assertEqual(agent.payload_var_name, "result_var")
        self.assertEqual(agent.max_iterations, 5)
        self.assertEqual(agent.execution_id, "exec-123")

    def test_enter_without_goals_does_not_call_save_goals(self):
        agent = AgentElement(goals="goal_var")

        message = MagicMock()
        message.read_context.return_value = "inherited ctx"
        message.mcp_services = {"svc": object()}
        message.get_var.return_value = ""  # No goals set

        with patch.object(AgentElement, "run_agent", return_value=message) as mock_run_agent, \
                patch("src.chainplate.agent.agent_data.AgentData.save_goals", new=MagicMock()) as mock_save_goals:

            result = agent.enter(message)

            self.assertIs(result, message)
            self.assertEqual(agent.inherited_context, "inherited ctx")
            self.assertEqual(agent.mcp_services, message.mcp_services)
            mock_run_agent.assert_called_once_with(message)
            mock_save_goals.assert_not_called()

    def test_enter_with_goals_calls_save_goals_and_run_agent(self):
        agent = AgentElement(goals="goal_var")

        message = MagicMock()
        message.read_context.return_value = "pipeline context"
        message.mcp_services = {}
        message.get_var.return_value = "Achieve objective X"

        with patch.object(AgentElement, "run_agent", return_value=message) as mock_run_agent, \
             patch("src.chainplate.agent.agent_data.AgentData.save_goals", new=MagicMock()) as mock_save_goals:

            result = agent.enter(message)

            self.assertIs(result, message)
            self.assertEqual(agent.inherited_context, "pipeline context")
            mock_run_agent.assert_called_once_with(message)
            # Given current implementation, save_goals is (incorrectly) called with only the goals string.
            mock_save_goals.assert_called_once_with("Achieve objective X")

    # --- New tests for run_agent_iteration ---
    def test_run_agent_iteration_incomplete(self):
        """run_agent_iteration should return (False, message) when action processing not complete."""
        agent = AgentElement()
        agent.agent_environment.send_to_user = MagicMock()
        message = MagicMock(name="MessageMock")

        action_text = '{"some": "json"}'
        action_obj = {"parsed": True}

        with patch.object(agent, 'get_next_action_text', return_value=action_text) as mock_get_next_action_text, \
             patch.object(agent, 'convert_action_text_to_object', return_value=action_obj) as mock_convert_action_text_to_object, \
             patch.object(agent, 'process_action_object', return_value=(False, message)) as mock_process_action_object:

            is_complete, returned_message = agent.run_agent_iteration(message)

        agent.agent_environment.send_to_user.assert_called_once_with("Thinking about my next action...")
        mock_get_next_action_text.assert_called_once_with(message)
        mock_convert_action_text_to_object.assert_called_once_with(action_text)
        mock_process_action_object.assert_called_once_with(action_obj, message)
        self.assertFalse(is_complete)
        self.assertIs(returned_message, message)
        self.assertEqual(agent.next_action_text, action_text)

    def test_run_agent_iteration_complete(self):
        """run_agent_iteration should return (True, new_message) when action processing completes the task."""
        agent = AgentElement()
        agent.agent_environment.send_to_user = MagicMock()
        message = MagicMock(name="OriginalMessage")
        completed_message = MagicMock(name="CompletedMessage")

        action_text = '{"complete": true}'
        action_obj = {"complete": True}

        with patch.object(agent, 'get_next_action_text', return_value=action_text) as mock_get_next_action_text, \
             patch.object(agent, 'convert_action_text_to_object', return_value=action_obj) as mock_convert_action_text_to_object, \
             patch.object(agent, 'process_action_object', return_value=(True, completed_message)) as mock_process_action_object:

            is_complete, returned_message = agent.run_agent_iteration(message)

        agent.agent_environment.send_to_user.assert_called_once_with("Thinking about my next action...")
        mock_get_next_action_text.assert_called_once_with(message)
        mock_convert_action_text_to_object.assert_called_once_with(action_text)
        mock_process_action_object.assert_called_once_with(action_obj, message)
        self.assertTrue(is_complete)
        self.assertIs(returned_message, completed_message)
        self.assertEqual(agent.next_action_text, action_text)

if __name__ == "__main__":
    unittest.main()
