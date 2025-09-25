import unittest
import time
from unittest.mock import patch, Mock
from chainplate.agent.agent_environment import (
    AgentEnvironment, ASSISTANT_ROLE, USER_ROLE, CHAT_CHANNEL_ID,
    DB_POLL_INTERVAL, WAIT_FOR_USER_INPUT_TIMEOUT
)
from chainplate.services.data.data_service import DataService


class TestAgentEnvironment(unittest.TestCase):
    def setUp(self):
        # fresh in-memory DB for each test
        self.data_service = DataService(":memory:")
        self.execution_id = self.data_service.create_execution("test-code")
        self.env = AgentEnvironment(execution_id=self.execution_id, data_service=self.data_service)

    def test_initialization_with_custom_data_service(self):
        """Test AgentEnvironment initialization with custom DataService."""
        custom_ds = DataService(":memory:")
        custom_exec_id = custom_ds.create_execution("custom-test")
        env = AgentEnvironment(execution_id=custom_exec_id, data_service=custom_ds)
        
        self.assertEqual(env.execution_id, custom_exec_id)
        self.assertEqual(env.data_service, custom_ds)

    def test_initialization_with_default_data_service(self):
        """Test AgentEnvironment initialization creates default DataService when none provided."""
        env = AgentEnvironment(execution_id=123)
        
        self.assertEqual(env.execution_id, 123)
        self.assertIsNotNone(env.data_service)
        # Default should be in-memory
        self.assertIsInstance(env.data_service, DataService)

    def test_initialization_creates_execution_when_none_provided(self):
        """Test AgentEnvironment creates execution when none provided."""
        env = AgentEnvironment(data_service=DataService(":memory:"))
        
        self.assertIsNotNone(env.execution_id)
        # Should be able to retrieve the created execution
        exec_row, steps = env.data_service.get_execution_with_steps(env.execution_id)
        self.assertIsNotNone(exec_row)
        self.assertEqual(steps, [])

    def test_send_to_user_creates_step(self):
        """Test send_to_user creates a proper execution step."""
        content = "Hello user"
        step_id = self.env.send_to_user(content)
        
        _, steps = self.data_service.get_execution_with_steps(self.execution_id)
        self.assertEqual(len(steps), 1)
        step = steps[0]
        self.assertEqual(step["id"], step_id)
        self.assertEqual(step["content"], content)
        self.assertEqual(step["role"], ASSISTANT_ROLE)
        self.assertEqual(step["channel"], CHAT_CHANNEL_ID)
        self.assertEqual(step["requires_input"], 0)
        self.assertIsNone(step["response_to"])

    def test_send_to_user_with_empty_content(self):
        """Test send_to_user works with empty content."""
        step_id = self.env.send_to_user("")
        
        _, steps = self.data_service.get_execution_with_steps(self.execution_id)
        self.assertEqual(len(steps), 1)
        step = steps[0]
        self.assertEqual(step["content"], "")
        self.assertEqual(step["role"], ASSISTANT_ROLE)

    def test_send_to_user_with_default_empty_content(self):
        """Test send_to_user works with default empty content parameter."""
        step_id = self.env.send_to_user()
        
        _, steps = self.data_service.get_execution_with_steps(self.execution_id)
        self.assertEqual(len(steps), 1)
        step = steps[0]
        self.assertEqual(step["content"], "")

    def test_get_user_input_creates_requiring_input_step_and_polls(self):
        """Test get_user_input creates step requiring input and polls for response."""
        prompt = "Enter your name"
        
        # Mock the polling to avoid actual waiting
        with patch.object(self.env, 'poll_for_user_input', return_value="John Doe") as mock_poll:
            result = self.env.get_user_input(prompt)
            
            # Verify a step requiring input was created
            _, steps = self.data_service.get_execution_with_steps(self.execution_id)
            self.assertEqual(len(steps), 1)
            step = steps[0]
            self.assertEqual(step["content"], prompt)
            self.assertEqual(step["role"], ASSISTANT_ROLE)
            self.assertEqual(step["channel"], CHAT_CHANNEL_ID)
            self.assertEqual(step["requires_input"], 1)
            
            # Verify polling was called with the step ID
            mock_poll.assert_called_once_with(step["id"], WAIT_FOR_USER_INPUT_TIMEOUT)
            self.assertEqual(result, "John Doe")

    def test_get_user_input_with_empty_prompt(self):
        """Test get_user_input works with empty prompt."""
        with patch.object(self.env, 'poll_for_user_input', return_value="response") as mock_poll:
            result = self.env.get_user_input("")
            
            _, steps = self.data_service.get_execution_with_steps(self.execution_id)
            step = steps[0]
            self.assertEqual(step["content"], "")
            self.assertEqual(step["requires_input"], 1)

    def test_get_user_input_with_default_empty_prompt(self):
        """Test get_user_input works with default empty prompt parameter."""
        with patch.object(self.env, 'poll_for_user_input', return_value="response") as mock_poll:
            result = self.env.get_user_input()
            
            _, steps = self.data_service.get_execution_with_steps(self.execution_id)
            step = steps[0]
            self.assertEqual(step["content"], "")

    def test_poll_for_user_input_returns_response(self):
        """Test poll_for_user_input returns user response when available."""
        # Create a step requiring input
        step_id = self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content="Enter value",
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=True,
        )
        
        # Simulate user reply
        reply_text = "42"
        self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content=reply_text,
            role=USER_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=False,
            response_to=step_id,
        )
        
        # Poll for the response
        result = self.env.poll_for_user_input(step_id, timeout=1, poll_interval=0.01)
        self.assertEqual(result, reply_text)

    def test_poll_for_user_input_timeout(self):
        """Test poll_for_user_input returns empty string on timeout."""
        # Create step requiring input but do not provide response
        step_id = self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content="Need input",
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=True,
        )
        
        start = time.time()
        result = self.env.poll_for_user_input(step_id, timeout=0.05, poll_interval=0.01)
        duration = time.time() - start
        
        self.assertEqual(result, "")
        # Ensure we respected timeout (with small cushion)
        self.assertLess(duration, 0.5)

    def test_poll_for_user_input_with_custom_poll_interval(self):
        """Test poll_for_user_input respects custom poll interval."""
        step_id = self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content="Need input",
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=True,
        )
        
        # Mock time.sleep to verify poll interval is used
        with patch('time.sleep') as mock_sleep:
            # Set a very short timeout to ensure we hit it
            result = self.env.poll_for_user_input(step_id, timeout=0.01, poll_interval=0.005)
            
            # Should have called sleep with our custom interval
            mock_sleep.assert_called_with(0.005)

    def test_poll_for_user_input_stops_when_response_found(self):
        """Test poll_for_user_input stops polling once response is found."""
        step_id = self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content="Enter value",
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=True,
        )
        
        # Create a mock that returns empty first, then a response
        responses = ["", "Found response"]
        with patch.object(self.env, 'check_for_user_input', side_effect=responses):
            result = self.env.poll_for_user_input(step_id, timeout=10, poll_interval=0.01)
            
            self.assertEqual(result, "Found response")

    def test_check_for_user_input_returns_content_when_response_exists(self):
        """Test check_for_user_input returns content when response step exists."""
        # Create prompt step
        step_id = self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content="Enter value",
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=True,
        )
        
        # Create response step
        response_content = "User response"
        self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content=response_content,
            role=USER_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=False,
            response_to=step_id,
        )
        
        result = self.env.check_for_user_input(step_id)
        self.assertEqual(result, response_content)

    def test_check_for_user_input_returns_empty_when_no_response(self):
        """Test check_for_user_input returns empty string when no response exists."""
        step_id = self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content="Enter value",
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=True,
        )
        
        result = self.env.check_for_user_input(step_id)
        self.assertEqual(result, "")

    def test_check_for_user_input_returns_empty_when_response_has_no_content(self):
        """Test check_for_user_input returns empty string when response step has no content."""
        step_id = self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content="Enter value",
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=True,
        )
        
        # Create response step with empty content
        self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content="",
            role=USER_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=False,
            response_to=step_id,
        )
        
        result = self.env.check_for_user_input(step_id)
        self.assertEqual(result, "")

    def test_check_for_user_input_returns_empty_when_response_has_none_content(self):
        """Test check_for_user_input returns empty string when response step has None content."""
        step_id = self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content="Enter value",
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=True,
        )
        
        # Create response step with None content
        self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content=None,
            role=USER_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=False,
            response_to=step_id,
        )
        
        result = self.env.check_for_user_input(step_id)
        self.assertEqual(result, "")

    def test_multiple_send_to_user_calls(self):
        """Test multiple send_to_user calls create separate steps."""
        messages = ["First message", "Second message", "Third message"]
        step_ids = []
        
        for msg in messages:
            step_id = self.env.send_to_user(msg)
            step_ids.append(step_id)
        
        _, steps = self.data_service.get_execution_with_steps(self.execution_id)
        self.assertEqual(len(steps), 3)
        
        for i, step in enumerate(steps):
            self.assertEqual(step["id"], step_ids[i])
            self.assertEqual(step["content"], messages[i])
            self.assertEqual(step["role"], ASSISTANT_ROLE)
            self.assertEqual(step["requires_input"], 0)

    def test_constants_are_properly_imported(self):
        """Test that module constants are properly defined and accessible."""
        self.assertEqual(ASSISTANT_ROLE, "assistant")
        self.assertEqual(USER_ROLE, "user")
        self.assertEqual(CHAT_CHANNEL_ID, 1)
        self.assertEqual(DB_POLL_INTERVAL, 2)
        self.assertEqual(WAIT_FOR_USER_INPUT_TIMEOUT, 300)

    def test_environment_isolation_between_instances(self):
        """Test that different AgentEnvironment instances with different execution IDs are properly isolated."""
        # Use the same data service but different executions to test logical isolation
        execution_id2 = self.data_service.create_execution("second-test")
        env2 = AgentEnvironment(execution_id=execution_id2, data_service=self.data_service)
        
        # Send messages from both environments
        self.env.send_to_user("Message from env1")
        env2.send_to_user("Message from env2")
        
        # Verify isolation - each execution should only have its own steps
        _, steps1 = self.data_service.get_execution_with_steps(self.execution_id)
        _, steps2 = self.data_service.get_execution_with_steps(execution_id2)
        
        self.assertEqual(len(steps1), 1)
        self.assertEqual(len(steps2), 1)
        self.assertEqual(steps1[0]["content"], "Message from env1")
        self.assertEqual(steps2[0]["content"], "Message from env2")
        self.assertEqual(steps1[0]["execution_id"], self.execution_id)
        self.assertEqual(steps2[0]["execution_id"], execution_id2)

    def test_default_execution_id_created_when_none_supplied(self):
        """Test that AgentEnvironment creates execution when none is provided."""
        env2 = AgentEnvironment(data_service=DataService(":memory:"))
        
        # Should have created an execution automatically
        self.assertIsNotNone(env2.execution_id)
        exec_row, steps = env2.data_service.get_execution_with_steps(env2.execution_id)
        self.assertIsNotNone(exec_row)
        self.assertEqual(steps, [])

    def test_get_user_input_timeout_returns_empty_string(self):
        """Test that get_user_input returns empty string when polling times out."""
        with patch.object(self.env, 'poll_for_user_input', return_value="") as mock_poll:
            result = self.env.get_user_input("Enter something")
            self.assertEqual(result, "")
            mock_poll.assert_called_once()

    def test_poll_for_user_input_handles_long_response_content(self):
        """Test that poll_for_user_input handles long response content correctly."""
        step_id = self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content="Enter a long response",
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=True,
        )
        
        # Create a very long response
        long_response = "A" * 10000
        self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content=long_response,
            role=USER_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=False,
            response_to=step_id,
        )
        
        result = self.env.poll_for_user_input(step_id, timeout=1, poll_interval=0.01)
        self.assertEqual(result, long_response)
        self.assertEqual(len(result), 10000)

    def test_check_for_user_input_with_nonexistent_step(self):
        """Test check_for_user_input with a step ID that doesn't exist."""
        # Use a step ID that doesn't exist
        result = self.env.check_for_user_input(99999)
        self.assertEqual(result, "")

    def test_send_to_user_returns_valid_step_id(self):
        """Test that send_to_user returns a valid integer step ID."""
        step_id = self.env.send_to_user("Test message")
        self.assertIsInstance(step_id, int)
        self.assertGreater(step_id, 0)

    def test_multiple_environments_same_execution_id(self):
        """Test that multiple AgentEnvironment instances with same execution ID work correctly."""
        # Create second environment with same execution ID
        env2 = AgentEnvironment(execution_id=self.execution_id, data_service=self.data_service)
        
        # Both should be able to send messages to the same execution
        step_id1 = self.env.send_to_user("Message from env1")
        step_id2 = env2.send_to_user("Message from env2")
        
        # Should have different step IDs
        self.assertNotEqual(step_id1, step_id2)
        
        # Both messages should be in the same execution
        _, steps = self.data_service.get_execution_with_steps(self.execution_id)
        self.assertEqual(len(steps), 2)
        contents = [step["content"] for step in steps]
        self.assertIn("Message from env1", contents)
        self.assertIn("Message from env2", contents)

    def test_get_user_input_with_special_characters(self):
        """Test get_user_input with special characters in prompt and response."""
        special_prompt = "Enter: <>&\"'\\n\\t"
        special_response = "Response: <>&#39;&quot;\\n\\t"
        
        with patch.object(self.env, 'poll_for_user_input', return_value=special_response) as mock_poll:
            result = self.env.get_user_input(special_prompt)
            
            # Verify the prompt was stored correctly
            _, steps = self.data_service.get_execution_with_steps(self.execution_id)
            prompt_step = steps[-1]  # Most recent step
            self.assertEqual(prompt_step["content"], special_prompt)
            
            # Verify the response was returned correctly
            self.assertEqual(result, special_response)


if __name__ == "__main__":
    unittest.main()
