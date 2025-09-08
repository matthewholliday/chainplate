from ...services.external.prompt_completion_services.openai_llm_provider import OpenAIPromptService
from ..agent_prompt_templates import GENERATE_PLAN, GENERATE_PLAN_SYSTEM

class GeneratePlanAction:

    def execute(self, context: str) -> str:
        return OpenAIPromptService().ask_question(
            system=GENERATE_PLAN_SYSTEM,
            question=f"{GENERATE_PLAN}\n\nContext:\n{context}"
        )