import unittest
from src.chainplate.elements.foreach_loop_element import ForEachLoopElement
from src.chainplate.message import Message

class DummyMessage(Message):
    def __init__(self, variables):
        self._variables = variables
    def get_var(self, key):
        return self._variables.get(key)

class TestForEachLoopElement(unittest.TestCase):
    def setUp(self):
        self.input_var = 'items'
        self.output_var = 'item'
        self.collection_str = 'a,b,c'
        self.variables = {self.input_var: self.collection_str}
        self.message = DummyMessage(self.variables)
        self.element = ForEachLoopElement(self.output_var, self.input_var)

    def test_enter_initializes_collection(self):
        self.element.enter(self.message)
        self.assertEqual(self.element.collection, ['a', 'b', 'c'])
        self.assertEqual(self.element.index, 0)

    def test_should_enter_true_and_false(self):
        self.element.enter(self.message)
        self.assertTrue(self.element.should_enter(self.message))
        self.element.index = 3
        self.assertFalse(self.element.should_enter(self.message))

    def test_get_current_item(self):
        self.element.enter(self.message)
        self.assertEqual(self.element.get_current_item(), 'a')
        self.element.index = 1
        self.assertEqual(self.element.get_current_item(), 'b')
        self.element.index = 2
        self.assertEqual(self.element.get_current_item(), 'c')
        with self.assertRaises(IndexError):
            self.element.index = 3
            self.element.get_current_item()

    def test_increment_iteration(self):
        self.element.enter(self.message)
        self.element.increment_iteration(self.message)
        self.assertEqual(self.element.index, 1)
        self.element.increment_iteration(self.message)
        self.assertEqual(self.element.index, 2)
        self.element.increment_iteration(self.message)
        self.assertEqual(self.element.index, 3)
        # Should not raise, and index should not exceed length
        self.element.increment_iteration(self.message)
        self.assertEqual(self.element.index, 3)

if __name__ == '__main__':
    unittest.main()
