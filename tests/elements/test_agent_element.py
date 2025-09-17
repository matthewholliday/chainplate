import unittest
from src.chainplate.elements.for_loop_element import ForLoopElement
from src.chainplate.message import Message
from src.chainplate.elements.agent_element import AgentElement

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

if __name__ == "__main__":
    unittest.main()
