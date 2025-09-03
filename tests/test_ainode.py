import unittest
from src.chainplate.ainode import AiNode
from src.chainplate.elements.pipeline_element import PipelineElement

class TestAiNode(unittest.TestCase):
    def test_pretty_print_no_error(self):
        # Should not raise error, even though it only prints
        AiNode.pretty_print(True, "pipeline", 1)
        AiNode.pretty_print(False, "pipeline", 2)

    def test_get_element_by_tag_all_tags(self):
        # Test all known tags return correct type
        tags = [
            ("pipeline", {}, PipelineElement),
            ("send-prompt", {"output_var": "x"}, __import__("src.chainplate.elements.send_prompt_element", fromlist=["SendPromptElement"]).SendPromptElement),
            ("set-variable", {"output_var": "x"}, __import__("src.chainplate.elements.set_variable_element", fromlist=["SetVariableElement"]).SetVariableElement),
            ("write-to-file", {"filename": "f.txt"}, __import__("src.chainplate.elements.write_to_file_element", fromlist=["WriteToFileElement"]).WriteToFileElement),
            ("context", {}, __import__("src.chainplate.elements.context_element", fromlist=["ContextElement"]).ContextElement),
            ("interpret-as-bool", {"output_var": "x", "input_var": "y"}, __import__("src.chainplate.elements.interpret_as_bool_element", fromlist=["InterpretAsBoolElement"]).InterpretAsBoolElement),
            ("interpret-as-integer", {"output_var": "x", "input_var": "y"}, __import__("src.chainplate.elements.interpret_as_integer", fromlist=["InterpretAsIntegerElement"]).InterpretAsIntegerElement),
            ("continue-if", {"condition": "true"}, __import__("src.chainplate.elements.continue_if_element", fromlist=["ContinueIfElement"]).ContinueIfElement),
            ("debug", {}, __import__("src.chainplate.elements.debug_element", fromlist=["DebugElement"]).DebugElement),
            ("apply-labels", {"output_var": "x", "input_var": "y"}, __import__("src.chainplate.elements.apply_labels_element", fromlist=["ApplyLabelsElement"]).ApplyLabelsElement),
            ("while-loop", {"condition": "true"}, __import__("src.chainplate.elements.while_loop_element", fromlist=["WhileLoopElement"]).WhileLoopElement),
            ("for-loop", {"from": 1, "to": 2}, __import__("src.chainplate.elements.for_loop_element", fromlist=["ForLoopElement"]).ForLoopElement),
            ("get-user-input", {"output_var": "x"}, __import__("src.chainplate.elements.get_user_input_element", fromlist=["GetUserInputElement"]).GetUserInputElement),
        ]
        for tag, attrs, cls in tags:
            el = AiNode.get_element_by_tag(tag, attrs, "content")
            self.assertIsInstance(el, cls)

    def test_enter_exit_with_none_element(self):
        node = AiNode(tag="t", contents="", children=[], attributes={}, element=None)
        msg = {}
        self.assertEqual(node.enter(msg, 0), msg)
        self.assertEqual(node.exit(msg, 0), msg)

    def test_execute_with_none_element(self):
        node = AiNode(tag="t", contents="", children=[], attributes={}, element=None)
        msg = {}
        # Should just return msg, no error
        self.assertEqual(node.execute(msg), msg)

    def test_execute_should_enter_false(self):
        class DummyElement:
            def enter(self, msg): return msg
            def exit(self, msg): return msg
            def should_enter(self, msg): return False
            def increment_iteration(self, msg): return msg
            def should_exit(self, msg): return True, msg
            def get_current_item(self): return None
        class DummyMessage(dict):
            def log_message(self, txt): self["logged"] = txt
        node = AiNode(tag="t", contents="", children=[], attributes={}, element=DummyElement())
        msg = DummyMessage()
        result = node.execute(msg)
        self.assertIn("logged", result)
        self.assertIn("Skipping element", result["logged"])

    def test_from_dict_nested_children(self):
        data = {
            "tag": "pipeline",
            "contents": "root",
            "attributes": {},
            "children": [
                {"tag": "debug", "contents": "child1", "attributes": {}, "children": []},
                {"tag": "debug", "contents": "child2", "attributes": {}, "children": [
                    {"tag": "debug", "contents": "grandchild", "attributes": {}, "children": []}
                ]}
            ]
        }
        node = AiNode.from_dict(data)
        self.assertEqual(node.tag, "pipeline")
        self.assertEqual(len(node.children), 2)
        self.assertEqual(node.children[1].children[0].contents, "grandchild")

    def test_str_deeply_nested(self):
        data = {
            "tag": "pipeline",
            "contents": "root",
            "attributes": {},
            "children": [
                {"tag": "debug", "contents": "child1", "attributes": {}, "children": [
                    {"tag": "debug", "contents": "grandchild1", "attributes": {}, "children": []}
                ]},
                {"tag": "debug", "contents": "child2", "attributes": {}, "children": []}
            ]
        }
        node = AiNode.from_dict(data)
        s = str(node)
        self.assertIn("grandchild1", s)
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