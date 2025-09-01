import unittest
import os
from src.aixml.ainode import AiNode
from src.aixml.message import Message

class TestWriteToFileElement(unittest.TestCase):
    def test_write_to_file_element(self):
        filename = "test_output.txt"
        content = "Hello, file!"
        data = {
            "tag": "write-to-file",
            "contents": content,
            "attributes": {"filename": filename},
            "children": []
        }
        node = AiNode.from_dict(data)
        msg = Message()
        node.execute(msg)
        # Check file exists and content is correct
        self.assertTrue(os.path.exists(filename))
        with open(filename, "r", encoding="utf-8") as f:
            file_content = f.read()
        self.assertEqual(file_content, content)
        os.remove(filename)

if __name__ == "__main__":
    unittest.main()
