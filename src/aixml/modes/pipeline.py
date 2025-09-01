from ..message import Message
from ..ainode import AiNode
from ..tree import TreeNode
import json
import os

class PipelineMode:
    def __init__(self, xml_string: str):
        json_str = TreeNode.get_xml_as_json_string(xml_string)
        data = json.loads(json_str)
        self.tree = AiNode.from_dict(data)
        self.termination_message = 'Execution complete. Log location: ' + os.path.abspath('logs/execution.log')

    def run(self, payload: str = "", chat_history=[]) -> tuple[str, list]:
        message = Message()
        message.set_payload(payload)
        message.set_chat_history(chat_history)

        # Run and display logs:
        print('')
        self.tree.execute(message)
        print('')
        print(self.termination_message)
        message.print_logs()

        output_payload = message.get_payload()
        output_chat_history = message.get_chat_history()

        return (output_payload, output_chat_history)