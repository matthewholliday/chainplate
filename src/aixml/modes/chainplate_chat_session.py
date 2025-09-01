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

            #Get input from the user...
            user_input_txt = input("User: ")

            #Check for special commands...
            if user_input_txt.lower() == 'exit':
                print("Exiting chat mode.")
                break
            elif user_input_txt == 'history':
                self.pretty_print_chat_history()
                continue

            #Process the user input through the workflow...
            message = Message()
            message.set_payload(user_input_txt)
            message.conversation_history = self.chat_history
            message = self.create_workflow().run(message)

            #Update the chat history with the latest user and assistant messages
            #IMORTANT NOTE (!) transformed_input may be different from user_input_txt depending on how the workflow is designed.
            transformed_input = message.get_chat_input()
            transformed_user_message_obj = create_user_message(transformed_input)
            self.chat_history.append(transformed_user_message_obj)

            #Update chat history with assistant response
            assistant_response_text = message.get_chat_response()
            assistant_response_obj = create_assistant_message(assistant_response_text)
            self.chat_history.append(assistant_response_obj)

            #Print the assistant response
            print(f"Assistant: {assistant_response_text}")

    def get_latest_message_content(self) -> object:
        if self.chat_history:
            return self.chat_history[-1]['content']
        return None

    def create_workflow(self) -> ChainplateWorkflow:
        return ChainplateWorkflow(self.xml_string)
    
    def pretty_print_chat_history(self):
        print("\n CHAT HISTORY:  \n")
        for msg in self.chat_history:
            role = msg['role']
            content = msg['content']
            print(f"{role.capitalize()}: {content}")
            print("-----")