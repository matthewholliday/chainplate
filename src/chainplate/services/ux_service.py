from abc import ABC, abstractmethod

class UXService(ABC):
    @abstractmethod
    def get_input_from_user(self, prompt: str) -> str:
        pass

    @abstractmethod
    def show_output_to_user(self, output: str) -> None:
        pass