from ..message import Message
from ..ainode import AiNode
from ..tree import TreeNode
import json
import os

class ChainplateWorkflow:
    def __init__(self, xml_string: str):
        json_str = TreeNode.get_xml_as_json_string(xml_string)
        data = json.loads(json_str)
        self.tree = AiNode.from_dict(data)
        self.termination_message = 'Execution complete. Log location: ' + os.path.abspath('logs/execution.log')

    def run(self, message: Message) -> Message:

        # TODO: return object with this info so caller can decide what to do.
        # Run and display logs:
        # print('')
        self.tree.execute(message)
        # print('')
        # print(self.termination_message)
        # message.print_logs()
        return message