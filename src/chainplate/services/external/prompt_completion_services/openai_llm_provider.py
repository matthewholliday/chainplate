from .prompt_completion_service_base import PromptCompletionService

try:  # pragma: no cover - import guarded for environments without openai
    from openai import OpenAI  # type: ignore
    _OPENAI_AVAILABLE = True
except Exception:  # broad except to cover ImportError and potential runtime issues
    OpenAI = None  # type: ignore
    _OPENAI_AVAILABLE = False

client = OpenAI() if _OPENAI_AVAILABLE else None

MODEL = "gpt-5-mini"  # TODO: make configurable

class OpenAIPromptService(PromptCompletionService):

    def get_completion(self, chat_history: list[object]) -> str:
        if not _OPENAI_AVAILABLE or client is None:
            raise Exception("OpenAI library is not available. Please ensure it is installed and properly configured.")
        resp = client.chat.completions.create(
            model=MODEL,
            messages=chat_history
        )
        return resp.choices[0].message.content
    
    def ask_question(self, system: str, question: str) -> str:
        chat_history = [
            {
                "role": "system",
                "content": system
            },
            {
                "role": "user",
                "content": question
            }
        ]
        response_text = self.get_completion(chat_history)
        return response_text
    