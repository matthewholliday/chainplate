import unittest
from src.chainplate.elements.interpret_as_json_element import InterpretAsJsonElement
from src.chainplate.message import Message


class TestInterpretAsJsonElement(unittest.TestCase):
    def test_execute_valid_json(self):
        element = InterpretAsJsonElement(output_var="result", input_var="input")
        message = Message()
        message.set_var("input", '{"foo": 123, "bar": "baz"}')
        result = element.execute(message)
        self.assertEqual(result.get_var("result"), {"foo": 123, "bar": "baz"})
        self.assertEqual(getattr(result, "status", None), "success")

    def test_execute_invalid_json(self):
        element = InterpretAsJsonElement(output_var="result", input_var="input")
        message = Message()
        message.set_var("input", 'not a json')
        result = element.execute(message)
        self.assertEqual(getattr(result, "status", None), "error")
        self.assertTrue(hasattr(result, "error"))

if __name__ == "__main__":
    unittest.main()
