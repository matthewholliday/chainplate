from .ux_service import UXService

class CLIService(UXService):
    def get_input_from_user(self, prompt):
        return input(prompt)
    
    def show_output_to_user(self, output):
        print(output)