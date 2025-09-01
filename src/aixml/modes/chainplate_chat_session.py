from .chainplate_workflow import ChainplateWorkflow
from ..helpers.prompt_helper import create_user_message, create_assistant_message
from ..message import Message

class ChainplateChatSession:
    def __init__(self, xml_string: str):
        self.xml_string = xml_string
        self.chat_history = []
    
    def run_interactive(self):
        print("Entering interactive chat mode. Type 'exit' to quit.")
        while True:

            user_input_obj = self.get_user_input_obj()
            self.chat_history.append(user_input_obj)

            #Check for exit condition
            if user_input_obj['content'].lower() == 'exit':
                print("Exiting chat mode.")
                break
            elif user_input_obj['content'].lower() == 'history':
                self.pretty_print_chat_history()
                continue

            message = Message()
            message.set_payload(user_input_obj['content'])
            message.conversation_history = self.chat_history
            message = self.create_workflow().run(message)
            
            # payload is assumed to be the assistant response
            assistant_response_text = message.get_payload()
            assistant_response_obj = create_assistant_message(assistant_response_text)
            self.chat_history.append(assistant_response_obj)

            print(f"Assistant: {assistant_response_text}")

    def get_latest_message_content(self) -> object:
        if self.chat_history:
            return self.chat_history[-1]['content']
        return None

    @staticmethod
    def get_user_input_obj() -> object:
        user_input = input("User: ")
        user_message = create_user_message(user_input)
        return user_message

    def create_workflow(self) -> ChainplateWorkflow:
        return ChainplateWorkflow(self.xml_string)
    
    def pretty_print_chat_history(self):
        for msg in self.chat_history:
            role = msg['role']
            content = msg['content']
            print(f"{role.capitalize()}: {content}")