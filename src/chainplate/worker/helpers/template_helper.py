import jinja2
from jinja2 import Environment, StrictUndefined, meta


class TemplateHelper2:
    @staticmethod
    def render_template(template_str, context):
        template = jinja2.Template(template_str)
        return template.render(context)
    

class TemplateHelper:
    # One shared environment for both parsing and rendering
    _env = Environment(undefined=StrictUndefined)  # StrictUndefined helps surface mistakes

    @classmethod
    def add_globals(cls, **kwargs):
        """Optional: register globals that are available in templates."""
        cls._env.globals.update(kwargs)

    @classmethod
    def has_bindings(cls,template_str: str, template_context: dict) -> bool:
        referenced_vars = TemplateHelper.get_template_vars(template_str)
        available_vars = template_context.keys()
        return all(var in available_vars for var in referenced_vars)

    @classmethod
    def render_template(cls, template_str: str, context: dict):
        template = cls._env.from_string(template_str)
        rendered_template = template.render(**context)
        return rendered_template
    
    #Checks bindings before rendering...
    @classmethod
    def safe_render_template(cls, template_str: str, template_context: dict):
        try:
            if(not isinstance(template_str, str)):
                template_str = str(template_str)
            cls.render_template(template_str, template_context)
        except jinja2.exceptions.UndefinedError as e:
            return f"Error attempting to render template: \n {str(e)}"
        if not cls.has_bindings(template_str, template_context):
            missing_vars = cls.get_template_vars(template_str, template_context)
            return f"Error attempting to render template: \n Missing variables for template rendering: {', '.join(missing_vars)}"
        return cls.render_template(template_str, template_context)

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

