import unittest
from src.aixml.message import Message

class TestMessage(unittest.TestCase):
    def test_message_logging(self):
        msg = Message()
        msg.log("Test log entry")
        self.assertIn("Test log entry", msg.get_logs())

    def test_message_vars(self):
        msg = Message()
        msg.set_var("key1", "value1")
        self.assertTrue(msg.has_var("key1"))
        self.assertEqual(msg.get_var("key1"), "value1")
        self.assertFalse(msg.has_var("key2"))
        self.assertIsNone(msg.get_var("key2"))

    def test_context_stack(self):
        msg = Message()
        msg.push_context("context1")
        msg.push_context("context2")
        self.assertEqual(msg.context_stack, ["context1", "context2"])
        self.assertEqual(msg.read_context(), "context1\ncontext2")
        popped = msg.pop_context()
        self.assertEqual(popped, "context2")
        self.assertEqual(msg.context_stack, ["context1"])

    def test_payload_and_chat(self):
        msg = Message()
        msg.set_payload("payload data")
        self.assertEqual(msg.get_payload(), "payload data")
        msg.set_chat_input("input")
        self.assertEqual(msg.get_chat_input(), "input")
        msg.set_chat_response("response")
        self.assertEqual(msg.get_chat_response(), "response")

    def test_log_message_format(self):
        msg = Message()
        log_entry = msg.log_message("Some log text")
        self.assertIn("Some log text", log_entry)
        self.assertIn("END LOG ENTRY", log_entry)