# WriteToFileElement: writes content to a file specified by filename

from ..message import Message
from ..helpers.template_helper import TemplateHelper
from .base_element import BaseElement

class WriteToFileElement(BaseElement):
	def __init__(self, filename, content):
		self.filename = filename or "output.txt"
		self.content = content

	def enter(self, message: Message) -> Message:
		# Render content with template variables from message
		try:
			rendered_content = self.apply_template(self.content, message)
			with open(self.filename, "w", encoding="utf-8") as f:
				f.write(rendered_content)
			return message
		except Exception as e:
			message.log(f"WriteToFileElement: ERROR writing to {self.filename}: {e}")
		return message

	def exit(self, message: Message) -> Message:
		return message
	
	def conditions_passed(self, message: Message) -> bool:
		return True

	def get_label(self) -> str:
		return f"WriteToFileElement(filename={self.filename}, content={self.content})"
	
	@staticmethod
	def get_tag() -> str:
		return "write-to-file"