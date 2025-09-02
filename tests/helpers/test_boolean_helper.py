import unittest
from src.aixml.helpers.boolean_helper import BooleanHelper

class TestBooleanHelper(unittest.TestCase):
    def test_to_bool_true(self):
        for val in ["true", "True", "1", "yes", "on", " YES "]:
            self.assertTrue(BooleanHelper.to_bool(val))

    def test_to_bool_false(self):
        for val in ["false", "False", "0", "no", "off", " No "]:
            self.assertFalse(BooleanHelper.to_bool(val))

    def test_to_bool_invalid(self):
        with self.assertRaises(ValueError):
            BooleanHelper.to_bool("maybe")
        with self.assertRaises(ValueError):
            BooleanHelper.to_bool("")

    def test_is_bool(self):
        self.assertTrue(BooleanHelper.is_bool("yes"))
        self.assertTrue(BooleanHelper.is_bool("no"))
        self.assertFalse(BooleanHelper.is_bool("maybe"))

    def test_is_true(self):
        self.assertTrue(BooleanHelper.is_true("on"))
        self.assertFalse(BooleanHelper.is_true("off"))

    def test_is_false(self):
        self.assertTrue(BooleanHelper.is_false("off"))
        self.assertFalse(BooleanHelper.is_false("on"))

if __name__ == "__main__":
    unittest.main()
