from .chainplate_workflow import ChainplateWorkflow
from ..helpers.prompt_helper import create_user_message, create_assistant_message
from ..message import Message
from ..services.cli_service import CLIService

def print_ascii_art():
    art = r"""
 ██████ ██   ██  █████  ██ ███    ██ ██████  ██       █████  ████████ ███████ 
██      ██   ██ ██   ██ ██ ████   ██ ██   ██ ██      ██   ██    ██    ██      
██      ███████ ███████ ██ ██ ██  ██ ██████  ██      ███████    ██    █████   
██      ██   ██ ██   ██ ██ ██  ██ ██ ██      ██      ██   ██    ██    ██      
 ██████ ██   ██ ██   ██ ██ ██   ████ ██      ███████ ██   ██    ██    ███████ 

 Chainplate (2025)
 Open Source Project

 Licensed under the MIT License
 https://opensource.org/licenses/MIT                                                                     
                                                                              
"""
    print(art)

if __name__ == "__main__":
    print_ascii_art()

class ChainplateChatSession:
    def __init__(self, xml_string: str): # Default to CLIService if no UX service is provided
        self.xml_string = xml_string
        self.chat_history = []
    
    def run_interactive(self, ux_service=CLIService()):
        print_ascii_art()
        while True:
            try:
                #Get input from the user...
                user_input_txt = ux_service.get_input_from_user("[USER]    >> ")

                #Check for special commands...
                if user_input_txt.lower() == 'exit':
                    ux_service.show_output_to_user("Exiting chat session. Goodbye!")
                    break
                elif user_input_txt == 'history':
                    self.pretty_print_chat_history(ux_service)
                    continue

                #Process the user input through the workflow...
                message = Message()
                message.set_payload(user_input_txt)
            
                # temp testing

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
                ux_service.show_output_to_user(f"[CHATBOT] >> {assistant_response_text}\n\n")
            except Exception as e:
                ux_service.show_output_to_user(f"An error occurred: {e}")
                break

    def get_latest_message_content(self) -> object:
        if self.chat_history:
            return self.chat_history[-1]['content']
        return None
    
    def create_workflow(self) -> ChainplateWorkflow:
        return ChainplateWorkflow(self.xml_string, mode="chat") #TODO - move "chat" to a constant or enum for modes
    
    def pretty_print_chat_history(self, ux_service=None):
        ux_service.show_output_to_user("\n CHAT HISTORY:  \n")
        for msg in self.chat_history:
            role = msg['role']
            content = msg['content']
            ux_service.show_output_to_user(f"{role.capitalize()}: {content}")
            ux_service.show_output_to_user("-----")