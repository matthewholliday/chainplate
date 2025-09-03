from .base_element import BaseElement
from ..message import Message
import os

class ReadFileElement(BaseElement):
    print("Current working directory:", os.getcwd())

    """
    Element to read the contents of a file and store it in a variable.
    Attributes:
        output_var (str): The name of the variable to store the file contents.
        path (str): The path to the file to read.
    """
    name = "read-file"
    required_props = ["output_var", "path"]

    def enter(self, message: Message) -> Message:
        output_var = self.props.get("output_var")
        path = self.props.get("path")
        if not output_var or not path:
            raise ValueError("Both 'output_var' and 'path' properties are required for read-file element.")
        try:
            with open(path, "r", encoding="utf-8") as f:
                file_contents = f.read()
        except Exception as e:
            file_contents = f"[Error reading file: {e}]"
        message.set_var(output_var, file_contents)
        return message

    def exit(self, message: Message) -> Message:
        return message
