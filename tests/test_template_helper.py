from unittest import TestCase
from src.aixml.helpers.template_helper import TemplateHelper

class TestAiNode(TestCase):
    def test_render_template(self):
        template_str = "Hello, {{ name }}!"
        context = {"name": "World"}
        result = TemplateHelper.render_template(template_str, context)
        assert result == "Hello, World!"

    def test_get_template_vars(self):
        template_str = "Hello, {{ name }}! Today is {{ day }}."
        vars = TemplateHelper.get_template_vars(template_str)
        print("template_vars:", vars)
        assert vars == ['day', 'name']