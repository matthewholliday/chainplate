from ..message import Message
from ..ainode import AiNode
from ..tree import TreeNode
from ..services.cli_service import CLIService
import json
import os

class ChainplateWorkflow:
    def __init__(self, xml_string: str, ux_service=CLIService()):
        json_str = TreeNode.get_xml_as_json_string(xml_string)
        data = json.loads(json_str)
        self.tree = AiNode.from_dict(data)
        self.termination_message = 'Execution complete. Log location: ' + os.path.abspath('logs/execution.log')
        self.ux_service = ux_service

    def run(self, message: Message) -> Message:

        # TODO: return object with this info so caller can decide what to do.
        # Run and display logs:
        self.ux_service.show_output_to_user('')

        self.tree.execute(message)
        
        self.ux_service.show_output_to_user('')
        self.ux_service.show_output_to_user(self.termination_message)
        message.print_logs()
        return message