from ..message import Message
from ..helpers.template_helper import TemplateHelper
from .base_element import BaseElement

class DebugElement(BaseElement):
	def __init__(self, content="Debug Message"):
		self.content = content

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