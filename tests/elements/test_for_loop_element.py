import unittest
from src.aixml.elements.for_loop_element import ForLoopElement
from src.aixml.message import Message

class TestForLoopElement(unittest.TestCase):
    def setUp(self):
        self.start_num = "0"
        self.stop_num = "3"
        self.for_loop = ForLoopElement(self.start_num, self.stop_num)
        self.message = Message()

    def test_enter_sets_iteration_values(self):
        msg = self.for_loop.enter(self.message)
        self.assertEqual(self.for_loop.current_iteration_int, 0)
        self.assertEqual(self.for_loop.stop_num_int, 3)
        self.assertEqual(self.for_loop.current_iteration_evaluated, "0")
        self.assertEqual(self.for_loop.stop_num_evaluated, "3")
        self.assertIsInstance(msg, Message)

    def test_increment_iteration(self):
        self.for_loop.enter(self.message)
        msg = self.for_loop.increment_iteration(self.message)
        self.assertEqual(self.for_loop.current_iteration_int, 1)
        self.assertEqual(msg.get_var("index"), 1)

    def test_should_exit_false(self):
        self.for_loop.enter(self.message)
        should_exit, _ = self.for_loop.should_exit(self.message)
        self.assertFalse(should_exit)

    def test_should_exit_true(self):
        self.for_loop.enter(self.message)
        self.for_loop.current_iteration_int = 3
        should_exit, _ = self.for_loop.should_exit(self.message)
        self.assertTrue(should_exit)

    def test_enter_with_invalid_values(self):
        loop = ForLoopElement("not_an_int", "also_not_an_int")
        msg = loop.enter(self.message)
        logs = msg.get_logs()
        self.assertTrue(any("ForLoopElement encountered an error" in log for log in logs))

if __name__ == "__main__":
    unittest.main()
