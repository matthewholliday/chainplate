from ..message import Message
from ..helpers.template_helper import TemplateHelper
from .base_element import BaseElement
from ..execution_context import ExecutionContext

class DebugElement(BaseElement):
	def __init__(self, content="Debug Message", context: ExecutionContext = None):
		super().__init__(context=context)
		self.content = content
		self.context = context

	def enter(self, message: Message) -> Message:
		try:
			rendered_content = TemplateHelper.render_template(self.content, message.get_vars())			
			print(" >> " + rendered_content)
			return message
		except Exception as e:
			print("XML Element '<debug>' encountered an error: " + str(e))
			message.log_message(f"XML Element '<debug>' encountered an error: {e}")
		return message

	def exit(self, message: Message) -> Message:
		return message
	
	def get_label(self) -> str:
		return f"DebugElement(content={self.content})"
	
	@staticmethod
	def get_tag() -> str:
		return "debug"