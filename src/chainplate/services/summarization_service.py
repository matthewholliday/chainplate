from .external.prompt_completion_services.openai_llm_provider import OpenAIPromptService

SUMMARIZATION_SYSTEM = "You are an expert AI assistant specializing in text summarization."

SUMMARIZATION_PROMPT = """
Instruction:

You are an AI summarization assistant. Your task is to distill the following text into a concise summary that captures essential information for the AI agent's working memory.

Guidelines:

Content: Focus on key facts, decisions, and critical information.

Clarity: Use clear and unambiguous language.

Objectivity: Only be descriptive; do not include any analysis, opinions, or suggestions.

Format: Present the summary as a bullet-point list.

Do not include what is ABSENT from the text. If the text is empty or lacks substantive content, respond with "No content to summarize."

Text to Summarize:
"""

class SummarizationService:
    def __init__(self, prompt_service = OpenAIPromptService()):
        self.prompt_service = prompt_service

    def summarize(self, text: str) -> str:
        prompt = SUMMARIZATION_PROMPT + "\n\n" + text
        summary = self.prompt_service.ask_question(SUMMARIZATION_SYSTEM, prompt)
        return summary