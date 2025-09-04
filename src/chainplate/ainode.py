from dataclasses import dataclass, field
from typing import List, Any, Dict

from .message import Message

from .elements.pipeline_element import PipelineElement
from .elements.send_prompt_element import SendPromptElement
from .elements.interpret_as_bool_element import InterpretAsBoolElement
from .elements.context_element import ContextElement
from .elements.interpret_as_integer import InterpretAsIntegerElement
from .elements.while_loop_element import WhileLoopElement
from .elements.for_loop_element import ForLoopElement
from .elements.foreach_loop_element import ForEachLoopElement
from .elements.apply_labels_element import ApplyLabelsElement
from .elements.get_user_input_element import GetUserInputElement
from .elements.extract_list import ExtractList
from .elements.set_payload import SetPayloadElement
from .elements.store_memory import StoreMemory
from .elements.get_context_element import GetContextElement
from .elements.with_memory import WithMemoryElement
from .elements.read_file_element import ReadFileElement
from .elements.mcp_list_tools import MCPListToolsElement


@dataclass
class AiNode:
    tag: str
    contents: str
    children: List["AiNode"] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    element: Any = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AiNode":
        """Recursively build a AiNode tree from a dict."""

        tag = data["tag"]
        contents = data["contents"]
        attributes = data.get("attributes", {})
        children = [cls.from_dict(child) for child in data.get("children", [])]
        element = cls.get_element_by_tag(tag,attributes,contents)


        return cls(
            tag=tag,
            contents=contents,
            attributes=attributes,
            children=children,
            element = element
        )

    def __str__(self, level=0) -> str:
        """Pretty-print the tree for inspection."""
        indent = "  " * level
        result = f"{indent}{self.tag}: {self.contents!r}\n"
        for child in self.children:
            result += child.__str__(level + 1)
        return result
    
    #TODO - refactor to use a registry pattern instead of hardcoding all elements here...
    @staticmethod 
    def get_element_by_tag(tag: str, attributes, content) -> List["AiNode"]:
        if tag == "pipeline":
            return PipelineElement(attributes.get("name", "Unnamed Pipeline"))
        elif tag == "send-prompt":
            return SendPromptElement(
                output_var=attributes.get("output_var", "Unnamed Variable"),
                content=attributes.get("content", content)
            )
        elif tag == "set-variable":
            from .elements.set_variable_element import SetVariableElement
            return SetVariableElement(
                output_var=attributes.get("output_var", "Unnamed Variable"),
                content=content
            )
        elif tag == "write-to-file":
            from .elements.write_to_file_element import WriteToFileElement
            return WriteToFileElement(
                filename=attributes.get("filename", "output.txt"),
                content=content
            )
        elif tag == "context":
            return ContextElement(
                content=content
            )
        elif tag == "interpret-as-bool":
            return InterpretAsBoolElement(
                output_var=attributes.get("output_var", "Unnamed Variable"),
                input_var=attributes.get("input_var", "Unnamed Input")
            )
        elif tag == "interpret-as-integer":
            return InterpretAsIntegerElement(
                output_var=attributes.get("output_var", "Unnamed Variable"),
                input_var=attributes.get("input_var", "Unnamed Input")
            )
        elif tag == "continue-if":
            from .elements.continue_if_element import ContinueIfElement
            return ContinueIfElement(
                condition=attributes.get("condition", "false"),
                output_var=attributes.get("output_var", None)
            )
        elif tag == "debug":
            from .elements.debug_element import DebugElement
            return DebugElement(
                content=content or "Debug Message"
            )
        elif tag == "apply-labels": #TODO - rename
            return ApplyLabelsElement(
                output_var=attributes.get("output_var", "Unnamed Variable"),
                input_var=attributes.get("input_var", "Unnamed Input"),
                categories=attributes.get("labels", ""),
                criteria = attributes.get("criteria", "")
            )
        elif tag == "while-loop":
            element = WhileLoopElement(
                condition=attributes.get("condition", "false")
            )
            return element
        elif tag == "for-loop":
            element = ForLoopElement(
                start_num=int(attributes.get("from", 0)),
                stop_num=int(attributes.get("to", 10))
            )
            return element
        elif tag == "get-user-input":
            return GetUserInputElement(
                output_var=attributes.get("output_var", "Unnamed Variable"),
                content=content or "Please provide input: "
            )
        elif tag == "foreach-loop":
            return ForEachLoopElement(
                output_var=attributes.get("output_var", "Unnamed Variable"),
                input_var=attributes.get("input_var", "Unnamed Input")
            )
        elif tag == "extract-list":
            return ExtractList(
                output_var=attributes.get("output_var", "Unnamed Variable"),
                input_var=attributes.get("input_var", "Unnamed Input"),
                criteria=attributes.get("criteria", ""),
                content = content or "no input text provided"
            )
        elif tag == "read-file":
            element = ReadFileElement()
            element.props = {
                "output_var": attributes.get("output_var", "Unnamed Variable"),
                "path": attributes.get("path", "")
            }
            return element
        elif tag == "set-payload":
            element = SetPayloadElement(
                input_var=attributes.get("input_var", ""),
                content=content or ""
            )
            return element
        elif tag == "store-memory":
            element = StoreMemory(
                input_var=attributes.get("input_var", ""),
                content=content or ""
            )
            return element
        elif tag == "with-memory":
            element = WithMemoryElement()
            return element
        elif tag == "get-context":
            element = GetContextElement(
                output_var=attributes.get("output_var", "Unnamed Variable")
            )
            return element
        elif tag == "mcp-list-tools":
            element = MCPListToolsElement(
                output_var=attributes.get("output_var", "tool_list"),
                mcp_service=attributes.get("mcp_service", "notion")
            )
            return element
        else:
            raise ValueError(f"Unknown tag: {tag}")
            # return None # Placeholder for other elements
    
    @staticmethod
    def pretty_print(is_enter: bool, tag: str, depth: int):
        spacing = "  " * depth
        prefix = ">> " if is_enter else "<< "
        # print(spacing + prefix + f"{tag}") TODO - supply ux service

    def enter(self,message,depth) -> Message:
        AiNode.pretty_print(True,self.tag,depth)
        if(self.element):
            message = self.element.enter(message)
        return message

    def exit(self,message,depth) -> Message:
        AiNode.pretty_print(False,self.tag,depth - 1)
        if(self.element):
            message = self.element.exit(message)
        return message

    def execute(self,message,depth=0) -> Message:
        """Execute the node's action. Placeholder for actual logic."""
        message = self.enter(message,depth)
        depth += 1

        if self.element is None:
            return message

        # Check if conditions pass before running anything inside this element...
        should_enter = self.element.should_enter(message)

        if not should_enter:
            message.log_message(f"Skipping element <{self.tag}> as conditions not met.")
            message = self.exit(message,depth)
            return message
        
        # If you made it here, any initial entry checks passed, so process at least once...
        should_exit = False
        while not should_exit:
            message = self.element.increment_iteration(message) # For loops, etc.
            
            if self.element.get_current_item():
                message.set_var(self.element.output_var, self.element.get_current_item())

            for child in self.children:
                message = child.execute(message,depth) # Pass the message down the tree.

            # Check stop condition...
            should_exit, message = self.element.should_exit(message) # Returns true by default for non-repeating elements...
            

        # Exit logic runs for every element type...
        message = self.exit(message,depth)
        return message

    