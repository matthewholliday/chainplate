import unittest
from src.chainplate.helpers.list_helper import ListHelper


class TestListHelper(unittest.TestCase):
    def test_get_list_from_string_basic(self):
        s = "a, b, c"
        result = ListHelper.get_list_from_string(s)
        self.assertEqual(result, ["a", "b", "c"])

    def test_get_list_from_string_with_brackets(self):
        s = "[a, b, c]"
        result = ListHelper.get_list_from_string(s)
        self.assertEqual(result, ["a", "b", "c"])

    def test_get_list_from_string_with_parentheses(self):
        s = "(a, b, c)"
        result = ListHelper.get_list_from_string(s)
        self.assertEqual(result, ["a", "b", "c"])

    def test_get_list_from_string_with_braces(self):
        s = "{a, b, c}"
        result = ListHelper.get_list_from_string(s)
        self.assertEqual(result, ["a", "b", "c"])

    def test_get_list_from_string_empty(self):
        s = ""
        result = ListHelper.get_list_from_string(s)
        self.assertEqual(result, [])

    def test_get_list_from_string_spaces(self):
        s = "  a ,  b ,c  "
        result = ListHelper.get_list_from_string(s)
        self.assertEqual(result, ["a", "b", "c"])

    def test_get_list_from_string_single(self):
        s = "foo"
        result = ListHelper.get_list_from_string(s)
        self.assertEqual(result, ["foo"])

if __name__ == "__main__":
    unittest.main()
