import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from src.chainplate.services.mcp.mcp_service import MCPService

class TestMCPService(unittest.TestCase):
    def setUp(self):
        self.command = 'dummy_command'
        self.args = ['--dummy']
        self.env = {'DUMMY_ENV': '1'}
        self.mcp_service = MCPService(self.command, self.args, self.env)

    @patch('src.chainplate.services.mcp.mcp_service.asyncio.run')
    def test_initialize_calls_set_tools(self, mock_run):
        self.mcp_service.initialize()
        mock_run.assert_called_once()

    def test_get_stdio_params(self):
        params = MCPService.get_stdio_params(self.command, self.args, self.env)
        self.assertEqual(params.command, self.command)
        self.assertEqual(params.args, self.args)
        self.assertEqual(params.env, self.env)

    @patch('src.chainplate.services.mcp.mcp_service.MCPService.call_stdio_tool', new_callable=MagicMock)
    def test_call_tool(self, mock_call_tool):
        mock_call_tool.return_value = 'result'
        result = self.mcp_service.call_tool('tool_name', {'arg': 1})
        mock_call_tool.assert_called_once_with(self.mcp_service.server_params, 'tool_name', {'arg': 1})
        self.assertEqual(result, 'result')

    @patch('src.chainplate.services.mcp.mcp_service.MCPService.get_stdio_tools', new_callable=MagicMock)
    def test_list_tools(self, mock_get_stdio_tools):
        mock_get_stdio_tools.return_value = 'tools_list'
        result = self.mcp_service.list_tools()
        mock_get_stdio_tools.assert_called_once_with(self.mcp_service.server_params)
        self.assertEqual(result, 'tools_list')

    def test_set_tool(self):
        tool = MagicMock()
        tool.name = 'test_tool'
        tool.description = 'desc'
        tool.inputSchema = {'type': 'object'}
        tool.outputSchema = {'type': 'object'}
        tool.annotations = {'anno': True}
        self.mcp_service.set_tool(tool)
        self.assertIn('test_tool', self.mcp_service.tools)
        self.assertEqual(self.mcp_service.tools['test_tool']['description'], 'desc')
        self.assertEqual(self.mcp_service.tools['test_tool']['inputSchema'], {'type': 'object'})
        self.assertEqual(self.mcp_service.tools['test_tool']['outputSchema'], {'type': 'object'})
        self.assertEqual(self.mcp_service.tools['test_tool']['annotations'], {'anno': True})


import asyncio
from unittest import IsolatedAsyncioTestCase

class TestMCPServiceAsync(IsolatedAsyncioTestCase):
    def setUp(self):
        self.command = 'dummy_command'
        self.args = ['--dummy']
        self.env = {'DUMMY_ENV': '1'}
        self.server_params = MCPService.get_stdio_params(self.command, self.args, self.env)

    @patch('src.chainplate.services.mcp.mcp_service.stdio_client', new_callable=MagicMock)
    @patch('src.chainplate.services.mcp.mcp_service.ClientSession', new_callable=MagicMock)
    async def test_get_stdio_tools(self, mock_session, mock_stdio_client):
        # Setup mock session and tool
        mock_tool = MagicMock()
        mock_tool.name = 'tool1'
        mock_tool.description = 'desc1'
        mock_tool.inputSchema = {'type': 'object'}
        tools_obj = MagicMock()
        tools_obj.tools = [mock_tool]
        mock_session.return_value.__aenter__.return_value.list_tools = AsyncMock(return_value=tools_obj)
        mock_session.return_value.__aenter__.return_value.initialize = AsyncMock()
        mock_stdio_client.return_value.__aenter__.return_value = (MagicMock(), MagicMock())
        result = await MCPService.get_stdio_tools(self.server_params)
        self.assertIn('Tool name: tool1', result)

    @patch('src.chainplate.services.mcp.mcp_service.stdio_client', new_callable=MagicMock)
    @patch('src.chainplate.services.mcp.mcp_service.ClientSession', new_callable=MagicMock)
    async def test_call_stdio_tool(self, mock_session, mock_stdio_client):
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text='output text')]
        mock_session.return_value.__aenter__.return_value.call_tool = AsyncMock(return_value=mock_result)
        mock_session.return_value.__aenter__.return_value.initialize = AsyncMock()
        mock_stdio_client.return_value.__aenter__.return_value = (MagicMock(), MagicMock())
        result = await MCPService.call_stdio_tool(self.server_params, 'tool1', {'arg': 1})
        self.assertIn('output text', result)

    @patch('src.chainplate.services.mcp.mcp_service.stdio_client', new_callable=MagicMock)
    @patch('src.chainplate.services.mcp.mcp_service.ClientSession', new_callable=MagicMock)
    async def test_set_tools(self, mock_session, mock_stdio_client):
        mcp_service = MCPService(self.command, self.args, self.env)
        mock_tool = MagicMock()
        mock_tool.name = 'tool1'
        mock_tool.description = 'desc1'
        mock_tool.inputSchema = {'type': 'object'}
        mock_tool.outputSchema = {'type': 'object'}
        mock_tool.annotations = {'anno': True}
        tools_obj = MagicMock()
        tools_obj.tools = [mock_tool]
        mock_session.return_value.__aenter__.return_value.list_tools = AsyncMock(return_value=tools_obj)
        mock_session.return_value.__aenter__.return_value.initialize = AsyncMock()
        mock_stdio_client.return_value.__aenter__.return_value = (MagicMock(), MagicMock())
        await mcp_service.set_tools()
        self.assertIn('tool1', mcp_service.tools)

if __name__ == '__main__':
    unittest.main()
