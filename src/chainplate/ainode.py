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
from .elements.load_mcp_tools_element import LoadMCPToolsElement


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
        # List of element classes to check (all statically imported)
        from .elements.set_variable_element import SetVariableElement
        from .elements.write_to_file_element import WriteToFileElement
        from .elements.continue_if_element import ContinueIfElement
        from .elements.debug_element import DebugElement

        element_classes = [
            PipelineElement,
            SendPromptElement,
            ContextElement,
            InterpretAsBoolElement,
            InterpretAsIntegerElement,
            ApplyLabelsElement,
            WhileLoopElement,
            ForLoopElement,
            GetUserInputElement,
            ForEachLoopElement,
            ExtractList,
            ReadFileElement,
            SetPayloadElement,
            StoreMemory,
            WithMemoryElement,
            GetContextElement,
            SetVariableElement,
            WriteToFileElement,
            ContinueIfElement,
            DebugElement,
        ]

        for cls in element_classes:
            if hasattr(cls, "get_tag") and tag == cls.get_tag():
                # Instantiate with appropriate arguments
                if cls is PipelineElement:
                    return PipelineElement(attributes.get("name", "Unnamed Pipeline"))
                elif cls is SendPromptElement:
                    return SendPromptElement(
                        output_var=attributes.get("output_var", "Unnamed Variable"),
                        content=attributes.get("content", content)
                    )
                elif cls is ContextElement:
                    return ContextElement(content=content)
                elif cls is InterpretAsBoolElement:
                    return InterpretAsBoolElement(
                        output_var=attributes.get("output_var", "Unnamed Variable"),
                        input_var=attributes.get("input_var", "Unnamed Input")
                    )
                elif cls is InterpretAsIntegerElement:
                    return InterpretAsIntegerElement(
                        output_var=attributes.get("output_var", "Unnamed Variable"),
                        input_var=attributes.get("input_var", "Unnamed Input")
                    )
                elif cls is ApplyLabelsElement:
                    return ApplyLabelsElement(
                        output_var=attributes.get("output_var", "Unnamed Variable"),
                        input_var=attributes.get("input_var", "Unnamed Input"),
                        categories=attributes.get("labels", ""),
                        criteria=attributes.get("criteria", "")
                    )
                elif cls is WhileLoopElement:
                    return WhileLoopElement(
                        condition=attributes.get("condition", "false")
                    )
                elif cls is ForLoopElement:
                    return ForLoopElement(
                        start_num=int(attributes.get("from", 0)),
                        stop_num=int(attributes.get("to", 10))
                    )
                elif cls is GetUserInputElement:
                    return GetUserInputElement(
                        output_var=attributes.get("output_var", "Unnamed Variable"),
                        content=content or "Please provide input: "
                    )
                elif cls is ForEachLoopElement:
                    return ForEachLoopElement(
                        output_var=attributes.get("output_var", "Unnamed Variable"),
                        input_var=attributes.get("input_var", "Unnamed Input")
                    )
                elif cls is ExtractList:
                    return ExtractList(
                        output_var=attributes.get("output_var", "Unnamed Variable"),
                        input_var=attributes.get("input_var", "Unnamed Input"),
                        criteria=attributes.get("criteria", ""),
                        content=content or "no input text provided"
                    )
                elif cls is ReadFileElement:
                    element = ReadFileElement()
                    element.props = {
                        "output_var": attributes.get("output_var", "Unnamed Variable"),
                        "path": attributes.get("path", "")
                    }
                    return element
                elif cls is SetPayloadElement:
                    return SetPayloadElement(
                        input_var=attributes.get("input_var", ""),
                        content=content or ""
                    )
                elif cls is StoreMemory:
                    return StoreMemory(
                        input_var=attributes.get("input_var", ""),
                        content=content or ""
                    )
                elif cls is WithMemoryElement:
                    return WithMemoryElement()
                elif cls is GetContextElement:
                    return GetContextElement(
                        output_var=attributes.get("output_var", "Unnamed Variable")
                    )
                elif cls is SetVariableElement:
                    return SetVariableElement(
                        output_var=attributes.get("output_var", "Unnamed Variable"),
                        content=content
                    )
                elif cls is WriteToFileElement:
                    return WriteToFileElement(
                        filename=attributes.get("filename", "output.txt"),
                        content=content
                    )
                elif cls is ContinueIfElement:
                    return ContinueIfElement(
                        condition=attributes.get("condition", "false"),
                        output_var=attributes.get("output_var", None)
                    )
                elif cls is DebugElement:
                    return DebugElement(
                        content=content or "Debug Message"
                    )
                elif cls is LoadMCPToolsElement:
                    return LoadMCPToolsElement(
                        mcp_services_string=attributes.get("mcp_services", "")
                    )
        raise ValueError(f"Unknown tag: {tag}")
    
    @staticmethod
    def pretty_print(is_enter: bool, tag: str, depth: int):
        spacing = "  " * depth
        prefix = ">> " if is_enter else "<< "
        # print(spacing + prefix + f"{tag}") TODO - supply ux service

    def enter(self,message,depth) -> Message:
        AiNode.pretty_print(True,self.tag,depth)
        if(self.element):
            self.element.update_enter_logs(message)
            message = self.element.enter(message)
        return message

    def exit(self,message,depth) -> Message:
        AiNode.pretty_print(False,self.tag,depth - 1)
        if(self.element):
            message = self.element.exit(message)
        self.element.update_exit_logs(message)
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

    