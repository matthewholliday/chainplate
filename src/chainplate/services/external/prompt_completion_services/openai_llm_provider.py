from .prompt_completion_service_base import PromptCompletionService
from openai import OpenAI
client = OpenAI()
 
MODEL = "gpt-5-mini"  # TODO: make configurable

class OpenAIPromptService(PromptCompletionService):

    def get_completion(self, chat_history: list[object]) -> str:
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
    