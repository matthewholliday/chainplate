from .prompt_completion_services.openai_llm_provider import OpenAIPromptService

class ExternalServices:
    """A class to manage external services used in the application."""
    def __init__(self): # TODO: initialize from settings file
        self.prompt_service_name = "OPENAI"  # TODO: make configurable

    def get_prompt_service(self):
        if self.prompt_service_name == "OPENAI":
            return OpenAIPromptService()
        else:
            raise ValueError(f"Unsupported client name: {prompt_service_name}")