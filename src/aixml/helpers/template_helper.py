import jinja2

class TemplateHelper:
    @staticmethod
    def render_template(template_str, context):
        template = jinja2.Template(template_str)
        return template.render(context)
    
import jinja2
from jinja2 import Environment, StrictUndefined, meta

class TemplateHelper:
    # One shared environment for both parsing and rendering
    _env = Environment(undefined=StrictUndefined)  # StrictUndefined helps surface mistakes

    @classmethod
    def add_globals(cls, **kwargs):
        """Optional: register globals that are available in templates."""
        cls._env.globals.update(kwargs)

    @classmethod
    def render_template(cls, template_str: str, context: dict):
        template = cls._env.from_string(template_str)
        rendered_template = template.render(**context)
        return rendered_template

    @classmethod
    def get_template_vars(cls, template_str: str, provided: dict | None = None):
        """
        Return the names used in the template that are not provided via `provided`
        and not available as environment globals.
        """
        provided = provided or {}
        parsed = cls._env.parse(template_str)
        used = meta.find_undeclared_variables(parsed)

        # Remove what’s already available at render time
        already_available = set(cls._env.globals.keys()) | set(provided.keys())
        missing = used - already_available
        return sorted(missing)

