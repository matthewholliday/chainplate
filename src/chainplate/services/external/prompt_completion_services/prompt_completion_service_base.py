from abc import ABC, abstractmethod

class PromptCompletionService(ABC):

    @abstractmethod
    def get_completion(chat_history: list) -> str:
        pass