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
    
    def send_message(self, message: str) -> str:
        chat_history = [
            {"role": "user", "content": message}
        ]
        return self.get_completion(chat_history)