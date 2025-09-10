import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from .modes.chainplate_workflow import ChainplateWorkflow
from .modes.chainplate_chat_session import ChainplateChatSession
from .modes.chainplate_server import run_server
from .core import AIXMLCore  # your library function
from .message import Message

# TODO: Move most of this out of the __main__ file and into core.py or similar.

def _read_text(path: Path | None, encoding: str) -> str:
    if path is None:
        return sys.stdin.read()
    return path.read_text(encoding=encoding)

def _write_text(path: Path | None, data: str, encoding: str, overwrite: bool) -> None:
    if path is None:
        sys.stdout.write(data)
        if not data.endswith("\n"):
            sys.stdout.write("\n")
        return
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Refusing to overwrite existing file: {path}. Use --overwrite to allow."
        )
    path.write_text(data, encoding=encoding)

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="chainplate",
        description="Process AI-flavored XML: read input, run AIXMLCore.parse(), write output.",
    )
    p.add_argument("--encoding", default="utf-8", help="Text encoding (default: utf-8)")
    p.add_argument("--overwrite", action="store_true", help="Allow overwriting output file")
    p.add_argument("-a","--ask", type=str, help="Run an arbitrary query against the LLM")
    p.add_argument("-e","--execute", type=Path, help="Execute the XML instead of parsing")
    p.add_argument("-i", "--input", type=Path, help="Input file path (default: STDIN)")
    p.add_argument("-o", "--output", type=Path, help="Output file path (default: STDOUT)")
    p.add_argument("-p","--parse-to-json", action="store_true", help="Parse the XML and output JSON")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error messages")
    p.add_argument("--payload", type=str, help="Payload to pass into the execution")
    p.add_argument("--chat",type=Path, help="Run in chat mode with the given XML file")
    p.add_argument("--workflow", type=Path, help="TODO")
    p.add_argument("--server", action="store_true", help="Run the Chainplate server mode")
    p.add_argument("--list-mcp-services", action="store_true", help="List available MCP services from the config file")
    p.add_argument("--list-mcp-tools", action="store_true", help="List available MCP tools from the specified MCP server")
    p.add_argument("--mcp-service", type=str, help="Specify the MCP service to connect to for tool listing or calling")
    p.add_argument("--call-mcp-tool", type=str, help="Call a specific MCP tool by name")
    p.add_argument("--args", action="append", help="Key-value pairs for MCP tool arguments, e.g. --args key1=value1 --args key2=value2")
    p.add_argument("--agent", action="store_true", help="Run in agent mode to manage MCP services")
    p.add_argument("--agent-request", type=str, help="Make a request to the agent for a specific action or information")

    args = p.parse_args(argv)
    
    if(args.parse_to_json):
        print("Parsing mode activated.", file=sys.stderr)
        try:
            text = _read_text(args.input, args.encoding)
            result = AIXMLCore.parse(text)
            result = str(result)  # Convert result to string for output
            if not args.quiet:
                print(f"Type of result: {type(result)}", file=sys.stderr)

            _write_text(args.output, result, args.encoding, args.overwrite)
            if not args.quiet and args.output is not None:
                print(f"Wrote: {args.output}", file=sys.stderr)
            return 0
        except FileExistsError as e:
            print(str(e), file=sys.stderr)
            return 2
        except FileNotFoundError as e:
            print(f"File not found: {e}", file=sys.stderr)
            return 2
        except UnicodeError as e:
            print(f"Encoding error: {e}", file=sys.stderr)
            return 3
        except Exception as e:  # last-resort error with non-zero exit
            print('cut my life into pieces')
            print(f"Error: {e}", file=sys.stderr)
            return 1
    elif(args.execute):
        payload = args.payload if args.payload else ""
        xml_string = _read_text(args.execute, args.encoding)
        AIXMLCore.run_pipeline_mode(xml_string,payload)
        return 0
    elif(args.workflow):
        payload = args.payload if args.payload else ""
        workflow = ChainplateWorkflow(xml_string = _read_text(args.workflow, args.encoding))
        message = Message()
        message.set_payload(payload)
        workflow.run(message)
        return 0
    elif(args.chat):
        xml_string = _read_text(args.chat, args.encoding)
        chat_session = ChainplateChatSession(xml_string)
        chat_session.run_interactive()
    elif(args.server):
        run_server()
        return 0
    elif(args.ask):
        prompt = args.ask  # Use the string directly
        response = AIXMLCore.query(prompt)
        _write_text(args.output, response, args.encoding, args.overwrite)
        if not args.quiet and args.output is not None:
            print(f"Wrote: {args.output}", file=sys.stderr)
        return 0
    
if __name__ == "__main__":
    raise SystemExit(main())


# xml_string = "<root><child>data</child></root>"
# root_element = ET.fromstring(xml_string)
# tree = TreeNode.from_xml(root_element)
# Now 'tree' is a TreeNode instance representing the XML structure
