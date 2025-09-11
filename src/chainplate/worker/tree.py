class TreeNode:
    def __init__(self, tag, contents, attributes=None):
        self.tag = tag
        self.contents = contents.strip() if isinstance(contents, str) else contents
        self.children = []
        self.attributes = attributes if attributes is not None else {}

    def add_child(self, child_node):
        self.children.append(child_node)

    def to_json(self):
        return {
            "tag": self.tag,
            "contents": self.contents,
            "children": [child.to_json() for child in self.children],
            "attributes": self.attributes
        }
    
    def to_json_string(self):
        import json
        return json.dumps(self.to_json(), indent=2)

    @staticmethod
    def from_xml(xml_element) -> 'TreeNode':
        node = TreeNode(xml_element.tag, xml_element.text, xml_element.attrib)
        for child in xml_element:
            node.add_child(TreeNode.from_xml(child))
        return node
    
    @staticmethod
    def get_xml_as_json_string(xml_string: str) -> str:
        import xml.etree.ElementTree as ET
        root_element = ET.fromstring(xml_string)
        tree = TreeNode.from_xml(root_element)
        return tree.to_json_string()