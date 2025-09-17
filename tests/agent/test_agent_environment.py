import unittest
import time
from chainplate.agent.agent_environment import AgentEnvironment, ASSISTANT_ROLE, CHAT_CHANNEL_ID
from chainplate.services.data.data_service import DataService


class TestAgentEnvironment(unittest.TestCase):
    def setUp(self):
        # fresh in-memory DB for each test
        self.data_service = DataService(":memory:")
        self.execution_id = self.data_service.create_execution("test-code")
        self.env = AgentEnvironment(execution_id=self.execution_id, data_service=self.data_service)

    def test_send_to_user_creates_step(self):
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

    def test_get_user_input_returns_response(self):
        # Initiate prompt which creates a step requiring input
        prompt = "Enter value" 
        step_id = self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content=prompt,
            role=ASSISTANT_ROLE,
            channel=CHAT_CHANNEL_ID,
            requires_input=True,
        )
        # Simulate user reply (response_to references prompt step)
        reply_text = "42"
        self.data_service.add_execution_step(
            execution_id=self.execution_id,
            content=reply_text,
            role="user",
            channel=CHAT_CHANNEL_ID,
            requires_input=False,
            response_to=step_id,
        )
        # Directly poll for the created step id
        result = self.env.poll_for_user_input(step_id, timeout=1, poll_interval=0.01)
        self.assertEqual(result, reply_text)

    def test_poll_for_user_input_timeout(self):
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

    def test_default_execution_id_created_when_none_supplied(self):
        env2 = AgentEnvironment(data_service=DataService(":memory:"))
        # Should have at least the execution row; no steps yet
        exec_row, steps = env2.data_service.get_execution_with_steps(env2.execution_id)
        self.assertIsNotNone(exec_row)
        self.assertEqual(steps, [])


if __name__ == "__main__":
    unittest.main()
