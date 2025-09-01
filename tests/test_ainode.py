import unittest
from src.aixml.ainode import AiNode
from src.aixml.elements.pipeline_element import PipelineElement

class TestAiNode(unittest.TestCase):
    def test_from_dict(self):
        data = {
            "tag": "pipeline",
            "contents": "Content",
            "attributes": {"name": "my_pipeline"},
            "children": []
        }
        root = AiNode.from_dict(data)

        self.assertEqual(root.tag, "pipeline")
        self.assertEqual(root.contents, "Content")
        self.assertEqual(root.attributes, {"name": "my_pipeline"})
        self.assertTrue(isinstance(root.element, PipelineElement))

    def test_str_pretty_print(self):
        data = {
            "tag": "pipeline",
            "contents": "root",
            "attributes": {},
            "children": [
                {"tag": "debug", "contents": "child", "attributes": {}, "children": []}
            ]
        }
        node = AiNode.from_dict(data)
        s = str(node)
        self.assertIn("pipeline", s)
        self.assertIn("debug", s)

    def test_get_element_by_tag_known_and_unknown(self):
        # Known tag
        el = AiNode.get_element_by_tag("pipeline", {"name": "test"}, "content")
        self.assertIsInstance(el, PipelineElement)
        # Unknown tag
        with self.assertRaises(ValueError):
            AiNode.get_element_by_tag("unknown", {}, "")

    def test_enter_exit_conditions(self):
        class DummyElement:
            def enter(self, msg):
                msg["entered"] = True
                return msg
            def exit(self, msg):
                msg["exited"] = True
                return msg
            def conditions_passed(self, msg):
                return msg.get("pass", True)
        node = AiNode(tag="dummy", contents="", children=[], attributes={}, element=DummyElement())
        msg = {}
        msg = node.enter(msg, 0)
        self.assertTrue(msg["entered"])
        msg = node.exit(msg, 0)
        self.assertTrue(msg["exited"])
        self.assertTrue(node.conditions_passed({"pass": True}))
        self.assertFalse(node.conditions_passed({"pass": False}))

    def test_stop_condition_true(self):
        node = AiNode(tag="t", contents="", children=[], attributes={}, is_repeating=False)
        self.assertTrue(node.stop_condition_true({}))
        class DummyElement:
            def check_stop_condition_true(self, msg):
                return msg.get("stop", False)
        node2 = AiNode(tag="t", contents="", children=[], attributes={}, is_repeating=True, element=DummyElement())
        self.assertFalse(node2.stop_condition_true({}))
        self.assertTrue(node2.stop_condition_true({"stop": True}))

    def test_execute_runs_children(self):
        class DummyElement:
            def enter(self, msg): return msg
            def exit(self, msg): return msg
            def conditions_passed(self, msg): return True
        class DummyChild(AiNode):
            def execute(self, msg, depth=0):
                msg["ran_child"] = True
                return msg
        node = AiNode(tag="parent", contents="", children=[DummyChild(tag="c", contents="", children=[], attributes={})], attributes={}, element=DummyElement())
        # Make stop_condition_true return False first, then True (run loop once)
        call_count = {"count": 0}
        def stop_once(msg):
            if call_count["count"] == 0:
                call_count["count"] += 1
                return False
            return True
        node.stop_condition_true = stop_once
        msg = {}
        result = node.execute(msg)
        self.assertTrue(result.get("ran_child", False))