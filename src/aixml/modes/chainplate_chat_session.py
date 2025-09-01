from .chainplate_workflow import ChainplateWorkflow
from ..helpers.prompt_helper import create_user_message

class ChainplateChatSession:
    def __init__(self, xml_string: str):
        self.xml_string = xml_string
        self.chat_history = []
    
    def run_interactive(self):
        print("Entering interactive chat mode. Type 'exit' to quit.")
        while True:

            user_message = self.get_user_message()

            #Check for exit condition
            if user_message['content'].lower() == 'exit':
                print("Exiting chat mode.")
                break

            # Append user message to chat history
            self.chat_history.append(user_message)

            payload, self.chat_history = self.create_workflow().run(payload=user_message['content'], chat_history=self.chat_history)
            
            print(f"Assistant: {self.get_latest_message_content()['content']}")

    def get_latest_message_content(self) -> object:
        if self.chat_history:
            return self.chat_history[-1]['content']
        return None

    @staticmethod
    def get_user_message() -> object:
        user_input = input("User: ")
        user_message = create_user_message(user_input)
        return user_message

    def create_workflow(self) -> ChainplateWorkflow:
        return ChainplateWorkflow(self.xml_string)