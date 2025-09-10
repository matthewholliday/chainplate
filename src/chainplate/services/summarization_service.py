from .external.prompt_completion_services.openai_llm_provider import OpenAIPromptService

SUMMARIZATION_SYSTEM = "You are an expert AI assistant specializing in text summarization for AI agents."

SUMMARIZATION_PROMPT = """
Instruction:

You are an AI summarization assistant. Your task is to distill the following text into a concise summary that captures essential information for the AI agent's working memory.

Guidelines:

Length: Limit the summary to 3–5 bullet points, each no more than 20 words.

Content: Focus on key facts, decisions, and critical information.

Clarity: Use clear and unambiguous language.

Relevance: Include only information pertinent to the AI agent's tasks and objectives.

Format: Present the summary as a bullet-point list.

Text to Summarize:
"""

class SummarizationService:
    def __init__(self, prompt_service = OpenAIPromptService()):
        self.prompt_service = prompt_service

    def summarize(self, text: str) -> str:
        prompt = SUMMARIZATION_PROMPT + "\n\n" + text
        summary = self.prompt_service.ask_question(SUMMARIZATION_SYSTEM, prompt)
        return summary