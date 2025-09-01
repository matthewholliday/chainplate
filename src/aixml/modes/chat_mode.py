from ..message import Message
from ..ainode import AiNode

class ChatMode:
    def __init__(self, xml_string: str):
        json_str = AiNode.get_xml_as_json_string(xml_string)
        data = json.loads(json_str)
        self.tree = AiNode.from_dict(data)