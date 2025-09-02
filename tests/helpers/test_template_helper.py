from unittest import TestCase
from src.aixml.helpers.template_helper import TemplateHelper


class TestTemplateHelper(TestCase):
    def test_render_template(self):
        template_str = "Hello, {{ name }}!"
        context = {"name": "World"}
        result = TemplateHelper.render_template(template_str, context)
        self.assertEqual(result, "Hello, World!")

    def test_safe_render_template_success(self):
        template_str = "Hi, {{ who }}!"
        context = {"who": "Copilot"}
        result = TemplateHelper.safe_render_template(template_str, context)
        self.assertEqual(result, "Hi, Copilot!")

    def test_safe_render_template_missing_var(self):
        template_str = "Hi, {{ who }} and {{ missing }}!"
        context = {"who": "Copilot"}
        result = TemplateHelper.safe_render_template(template_str, context)
        self.assertIn("'missing' is undefined", result)

    def test_get_template_vars(self):
        template_str = "Hello, {{ name }}! Today is {{ day }}."
        vars = TemplateHelper.get_template_vars(template_str)
        self.assertEqual(vars, ['day', 'name'])