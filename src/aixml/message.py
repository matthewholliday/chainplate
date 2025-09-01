from .helpers.template_helper import TemplateHelper
from .helpers.prompt_helper import ask as prompt_ask
import os

CONTEXT_output_var = "__context__"

class Message:
    def __init__(self):
        self.logs = []
        self.vars = {}
        self.context_stack = []
        self.vars[CONTEXT_output_var] = self.read_context()

    def update_context_var(self):
        self.vars[CONTEXT_output_var] = self.read_context()
        return self

    def push_context(self, content: str):
        self.context_stack.append(content)
        self.update_context_var()
        return self

    def pop_context(self):
        if self.context_stack:
            return self.context_stack.pop()
        self.update_context_var()
        return self
    
    def read_context(self):
        context = "\n".join(self.context_stack)
        return context

    def log(self, message: str):
        self.logs.append(message)

    def get_logs(self):
        return self.logs
    
    def print_logs(self):
        # print all logs to logs/execution.log (overwrite instead of append)
        os.makedirs("logs", exist_ok=True)
        with open("logs/execution.log", "w", encoding="utf-8") as f:
            for log in self.logs:
                f.write(log + "\n")

    def set_var(self, key: str, value):
        self.log_variable(key, value)
        self.vars[key] = value
        return self

    def has_var(self, key: str) -> bool:
        return key in self.vars
    
    def get_var(self, key: str):
        return self.vars.get(key, None)
    
    def has_all_vars(self, keys: list) -> bool:
        return all(key in self.vars for key in keys)
    
    def has_template_bindings(self, template_str: str) -> bool:
        required_vars = TemplateHelper.get_template_vars(template_str)
        return self.has_all_vars(required_vars)
    
    def get_vars(self):
        return self.vars
    
    def get_formatted_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    def log_message(self, text: str):
        timestamp = self.get_formatted_timestamp()
        formatted_text = f"[{timestamp}]"
        formatted_text += "\n" + text
        self.log(formatted_text)
        self.log("===============END LOG ENTRY================")
        self.log("")  # Blank line for readability

    def log_variable(self, output_var: str, var_value: any):
        header_text = "[SET-VARIABLE]\n"
        variable_text = f"NAME: \n {output_var}\n"
        value_text =  f"VALUE: \n {var_value}"
        full_text = header_text + variable_text + "\n" + value_text
        self.log_message(full_text)

    def generate_prompt(self, prompt: str) -> str:
        context_str = self.read_context()
        prompt_with_context = f"{context_str}\n\n{prompt}" if context_str else prompt
        return prompt_with_context

    def ask_llm(self, prompt: str) -> str:
        prompt_with_context = self.generate_prompt(prompt)
        response = prompt_ask(prompt_with_context)
        return response
    
    def log_pipeline_start(self, pipeline_name: str):
        self.log_message(f"[PIPELINE START]\n{pipeline_name}")
        return self
    
    def log_pipeline_end(self, pipeline_name: str):
        self.log_message(f"[PIPELINE END]\n{pipeline_name}")
        return self
    
    def log_continue_if_start(self, element_name: str, condition: str, output_var: str = None):
        var_info = f" (var: {output_var})" if output_var else ""
        self.log_message(f"[CONTINUE-IF START]\nElement: {element_name}{var_info}, Condition: {condition}")
        return self
    
    def log_continue_if_end(self, element_name: str, condition: str, output_var: str = None):
        var_info = f" (var: {output_var})" if output_var else ""
        self.log_message(f"[CONTINUE-IF END]\nElement: {element_name}{var_info}, Condition: {condition}")
        return self
    
    def log_write_to_file(self, filename: str, content: str):
        self.log_message(f"[WRITE-TO-FILE]\nWrote content to file: {filename}\nContent:\n{content}")
        return self
    
    def log_debug_message(self, name, text: str):
        text = f"[DEBUG]\nElement: {name}\nMessage:{text}"
        self.log_message(text)
        return self
    
    def set_payload(self, payload: str):
        self.set_var("payload", payload)
        return self

