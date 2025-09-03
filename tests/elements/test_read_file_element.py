import unittest
from src.chainplate.elements.read_file_element import ReadFileElement
from src.chainplate.message import Message
import os

class TestReadFileElement(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_readfile.txt"
        self.test_content = "Hello, Chainplate!"
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(self.test_content)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)


    def test_read_file_success(self):
        props = {"output_var": "file_data", "path": self.test_file}
        element = ReadFileElement()
        element.props = props
        message = Message()
        result = element.enter(message)
        self.assertIn("file_data", result.get_vars())
        self.assertEqual(result.get_var("file_data"), self.test_content)


    def test_read_file_missing_file(self):
        props = {"output_var": "file_data", "path": "nonexistent.txt"}
        element = ReadFileElement()
        element.props = props
        message = Message()
        result = element.enter(message)
        self.assertIn("file_data", result.get_vars())
        self.assertTrue(result.get_var("file_data").startswith("[Error reading file:"))


    def test_missing_props(self):
        element = ReadFileElement()
        element.props = {"output_var": "file_data"}  # Missing path
        message = Message()
        with self.assertRaises(ValueError):
            element.enter(message)

if __name__ == "__main__":
    unittest.main()
