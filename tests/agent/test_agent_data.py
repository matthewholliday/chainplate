import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

from chainplate.agent.agent_data import AgentData


class TestAgentData(unittest.TestCase):
    def setUp(self):
        patcher = patch('chainplate.agent.agent_data.DataService')
        self.addCleanup(patcher.stop)
        self.mock_ds_class = patcher.start()
        self.mock_data_service = MagicMock()
        self.mock_ds_class.return_value = self.mock_data_service

        self.mock_data_service.get_agent_memory.return_value = [
            {"content": "memory line 1"},
            {"content": ""},
            {"content": "memory line 2"},
            {"content": None},
        ]
        self.mock_data_service.get_agent_goal.return_value = [
            {"content": "goal 1"},
            {"content": "goal 2"},
        ]
        self.mock_data_service.get_agent_plan.return_value = [
            {"content": "step 1"},
            {"content": ""},
            {"content": "step 2"},
        ]
        # default instance without execution id; individual tests may set one
        self.agent_data = AgentData()

    def test_concatenate_content_filters_and_joins(self):
        records = [
            {"content": "A"},
            {"content": ""},
            {"content": None},
            {"content": "B"},
        ]
        result = AgentData.concatenate_content(records)
        self.assertEqual(result, "A\nB")

    def test_concatenate_content_empty(self):
        self.assertEqual(AgentData.concatenate_content([]), "")

    def test_get_working_memory(self):
        self.agent_data.set_execution_id(42)
        result = self.agent_data.get_working_memory()
        self.mock_data_service.get_agent_memory.assert_called_once_with(42)
        self.assertEqual(result, "memory line 1\nmemory line 2")

    def test_get_goals(self):
        self.agent_data.set_execution_id(7)
        result = self.agent_data.get_goals()
        self.mock_data_service.get_agent_goal.assert_called_once_with(7)
        self.assertEqual(result, "goal 1\ngoal 2")

    def test_get_plan(self):
        self.agent_data.set_execution_id(9)
        result = self.agent_data.get_plan()
        self.mock_data_service.get_agent_plan.assert_called_once_with(9)
        self.assertEqual(result, "step 1\nstep 2")

    def test_get_services(self):
        message = SimpleNamespace(mcp_services={"svc1": object(), "svc2": object()})
        result = self.agent_data.get_services(message)
        self.assertEqual(result, "svc1, svc2")

    def test_save_goals(self):
        mock_ds = MagicMock()
        AgentData.save_goals(data_service=mock_ds, execution_id=11, goals="new goal")
        mock_ds.upsert_agent_goal_content.assert_called_once_with(11, "new goal")

    def test_save_plan(self):
        mock_ds = MagicMock()
        AgentData.save_plan(data_service=mock_ds, execution_id=22, plan="step A -> step B")
        mock_ds.upsert_agent_plan_content.assert_called_once_with(22, "step A -> step B")

if __name__ == '__main__':
    unittest.main()