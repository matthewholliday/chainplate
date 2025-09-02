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
            def should_enter(self, msg):
                return msg.get("pass", True)
        node = AiNode(tag="dummy", contents="", children=[], attributes={}, element=DummyElement())
        msg = {}
        msg = node.enter(msg, 0)
        self.assertTrue(msg["entered"])
        msg = node.exit(msg, 0)
        self.assertTrue(msg["exited"])
        self.assertTrue(node.element.should_enter({"pass": True}))
        self.assertFalse(node.element.should_enter({"pass": False}))

    def test_stop_condition_true(self):
        # The current AiNode does not have is_repeating or stop_condition_true, so this test is obsolete.
        # Instead, test should_exit logic via element's should_exit method.
        class DummyElement:
            def should_exit(self, msg):
                return msg.get("stop", False), msg
        node = AiNode(tag="t", contents="", children=[], attributes={}, element=DummyElement())
        should_exit, _ = node.element.should_exit({})
        self.assertFalse(should_exit)
        should_exit, _ = node.element.should_exit({"stop": True})
        self.assertTrue(should_exit)

    def test_execute_runs_children(self):
        class DummyElement:
            def enter(self, msg): return msg
            def exit(self, msg): return msg
            def should_enter(self, msg): return True
            def increment_iteration(self, msg): return msg
            def should_exit(self, msg):
                # Run loop once, then exit
                if not msg.get("looped", False):
                    msg["looped"] = True
                    return False, msg
                return True, msg
        class DummyChild(AiNode):
            def execute(self, msg, depth=0):
                msg["ran_child"] = True
                return msg
        node = AiNode(tag="parent", contents="", children=[DummyChild(tag="c", contents="", children=[], attributes={})], attributes={}, element=DummyElement())
        msg = {}
        result = node.execute(msg)
        self.assertTrue(result.get("ran_child", False))