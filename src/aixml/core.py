from .tree import TreeNode
from .ainode import AiNode
from .message import Message
from .helpers import prompt_helper
import json

class AIXMLCore:
    def __init__(self):
        pass

    @staticmethod
    def query(prompt: str) -> str:
        response = prompt_helper.ask_openai(prompt)
        return response

    @staticmethod
    def parse(xml_string: str) -> TreeNode:
        json_str = TreeNode.get_xml_as_json_string(xml_string)
        return json_str
    
    @staticmethod
    def run_pipeline_mode(xml_string: str, payload: str = "") -> None:
        import os

        json_str = TreeNode.get_xml_as_json_string(xml_string)
        data = json.loads(json_str)
        node = AiNode.from_dict(data)

        msg = Message()
        msg.set_payload(payload)

        print('AIXML: executing pipeline...')
        node.execute(msg)
        print('AIXML: execution complete. View logs: ' + os.path.abspath('logs/execution.log'))

        msg.print_logs()

    @staticmethod
    def run_chat_mode(xml_string: str) -> None:
        import os

        json_str = TreeNode.get_xml_as_json_string(xml_string)
        data = json.loads(json_str)
        tree = AiNode.from_dict(data)

        


