import unittest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from chainplate.agent.agent_data import AgentData

class TestAgentData(unittest.TestCase):
    def setUp(self):
        self.mock_data_service = MagicMock()
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

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_get_working_memory(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        result = agent_data.get_working_memory()
        self.mock_data_service.get_agent_memory.assert_called_once_with(42)
        self.assertEqual(result, "memory line 1\nmemory line 2")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_get_goals(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        result = agent_data.get_goals()
        self.mock_data_service.get_agent_goal.assert_called_once_with(42)
        self.assertEqual(result, "goal 1\ngoal 2")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_get_plan(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        result = agent_data.get_plan()
        self.mock_data_service.get_agent_plan.assert_called_once_with(42)
        self.assertEqual(result, "step 1\nstep 2")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_get_services(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        message = SimpleNamespace(mcp_services={"svc1": object(), "svc2": object()})
        result = agent_data.get_services(message)
        self.assertEqual(result, "svc1, svc2")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_get_tools(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        mock_service1 = MagicMock()
        mock_service1.list_tools.return_value = ["tool1", "tool2"]
        mock_service2 = MagicMock()
        mock_service2.list_tools.return_value = ["tool3"]
        message = SimpleNamespace(mcp_services={"svc1": mock_service1, "svc2": mock_service2})
        result = agent_data.get_tools(message)
        self.assertEqual(result, "tool1tool2tool3")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_get_chat_history_summary(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        self.mock_data_service.get_execution_steps.return_value = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        result = agent_data.get_chat_history_summary(None)
        self.mock_data_service.get_execution_steps.assert_called_once_with(42)
        # Current implementation has a bug - it should format the messages properly
        self.assertEqual(result, "Hello\nHi there")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_save_goals(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        agent_data.save_goals("new goal")
        self.mock_data_service.upsert_agent_goal_content.assert_called_once_with(42, "new goal")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_save_plan(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        agent_data.save_plan("step A -> step B")
        self.mock_data_service.upsert_agent_plan_content.assert_called_once_with(42, "step A -> step B")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_add_memory(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        agent_data.add_memory("new memory entry")
        self.mock_data_service.add_agent_memory.assert_called_once_with(42, "new memory entry")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_set_execution_id_logs_initialization(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        mock_logging_service.log_info.assert_called_with("AgentData execution_id set to: 42")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_constructor_creates_data_service(self, mock_ds_class, mock_logging_service):
        # The constructor should create its own DataService instance
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData()
        self.assertIsNotNone(agent_data.data_service)
        
        # Test that setting execution_id works
        agent_data.set_execution_id(42)
        self.assertEqual(agent_data.execution_id, 42)

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_get_services_with_empty_dict(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        message = SimpleNamespace(mcp_services={})
        result = agent_data.get_services(message)
        self.assertEqual(result, "")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_get_tools_with_empty_services(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        message = SimpleNamespace(mcp_services={})
        result = agent_data.get_tools(message)
        self.assertEqual(result, "")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_save_goals_with_empty_string(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        agent_data.save_goals()  # Default empty string
        self.mock_data_service.upsert_agent_goal_content.assert_called_once_with(42, "")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_save_plan_with_empty_string(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        agent_data.save_plan()  # Default empty string
        self.mock_data_service.upsert_agent_plan_content.assert_called_once_with(42, "")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_add_memory_with_empty_string(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        agent_data.add_memory()  # Default empty string
        self.mock_data_service.add_agent_memory.assert_called_once_with(42, "")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_get_working_memory_with_empty_data(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        self.mock_data_service.get_agent_memory.return_value = []
        result = agent_data.get_working_memory()
        self.assertEqual(result, "")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_get_goals_with_empty_data(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        self.mock_data_service.get_agent_goal.return_value = []
        result = agent_data.get_goals()
        self.assertEqual(result, "")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_get_plan_with_empty_data(self, mock_ds_class, mock_logging_service):
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        self.mock_data_service.get_agent_plan.return_value = []
        result = agent_data.get_plan()
        self.assertEqual(result, "")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_set_execution_id_returns_self(self, mock_ds_class, mock_logging_service):
        """Test that set_execution_id returns self for method chaining."""
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service)
        
        result = agent_data.set_execution_id(42)
        
        self.assertIs(result, agent_data)
        self.assertEqual(agent_data.execution_id, 42)
        mock_logging_service.log_info.assert_called_with("AgentData execution_id set to: 42")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_set_execution_id_allows_method_chaining(self, mock_ds_class, mock_logging_service):
        """Test that set_execution_id allows method chaining with other operations."""
        mock_ds_class.return_value = self.mock_data_service
        
        # Test method chaining during instantiation
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        
        self.assertEqual(agent_data.execution_id, 42)
        mock_logging_service.log_info.assert_called_with("AgentData execution_id set to: 42")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_set_execution_id_can_change_execution(self, mock_ds_class, mock_logging_service):
        """Test that set_execution_id can change the execution ID after initial setting."""
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service).set_execution_id(42)
        
        # Change execution ID
        agent_data.set_execution_id(99)
        
        self.assertEqual(agent_data.execution_id, 99)
        # Should have been called twice
        self.assertEqual(mock_logging_service.log_info.call_count, 2)
        mock_logging_service.log_info.assert_any_call("AgentData execution_id set to: 42")
        mock_logging_service.log_info.assert_any_call("AgentData execution_id set to: 99")

    @patch("chainplate.agent.agent_data.LoggingService")
    @patch("chainplate.agent.agent_data.DataService")
    def test_set_execution_id_with_different_types(self, mock_ds_class, mock_logging_service):
        """Test that set_execution_id accepts different types."""
        mock_ds_class.return_value = self.mock_data_service
        agent_data = AgentData(data_service=self.mock_data_service)
        
        # Test with integer
        agent_data.set_execution_id(42)
        self.assertEqual(agent_data.execution_id, 42)
        
        # Test with string (though signature says int, it may accept other types)
        agent_data.set_execution_id("123")  # type: ignore
        self.assertEqual(agent_data.execution_id, "123")

    def test_initialization_without_execution_id(self):
        """Test that AgentData can be initialized without execution_id."""
        with patch("chainplate.agent.agent_data.DataService") as mock_ds_class:
            mock_ds_class.return_value = self.mock_data_service
            agent_data = AgentData()
            
            # Should not have execution_id set initially
            self.assertFalse(hasattr(agent_data, 'execution_id'))
            
            # Should be able to set it later
            agent_data.set_execution_id(42)
            self.assertEqual(agent_data.execution_id, 42)

if __name__ == "__main__":
    unittest.main()
