import unittest
from src.aixml.message import Message

class TestMessage(unittest.TestCase):
    def test_message_logging(self):
        from src.aixml.message import Message
        msg = Message()
        msg.log("Test log entry")
        self.assertIn("Test log entry", msg.logs)
    
    def test_message_vars(self):
        msg = Message()
        msg.set_var("key1", "value1")
        self.assertTrue(msg.has_var("key1"))
        self.assertEqual(msg.get_var("key1"), "value1")
        self.assertFalse(msg.has_var("key2"))
        self.assertIsNone(msg.get_var("key2"))
        
        msg.set_var("key2", 42)
        self.assertTrue(msg.has_all_vars(["key1", "key2"]))
        self.assertFalse(msg.has_all_vars(["key1", "key3"]))

    def test_has_template_bindings(self):
        msg = Message()
        msg.set_var("name", "Alice")
        template_str = "Hello, {{ name }}!"
        self.assertTrue(msg.has_template_bindings(template_str))
        
        template_str_missing = "Hello, {{ name }}! Today is {{ day }}."
        self.assertFalse(msg.has_template_bindings(template_str_missing))