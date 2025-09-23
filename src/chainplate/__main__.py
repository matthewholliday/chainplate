import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from .modes.chainplate_workflow import ChainplateWorkflow
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
    p.add_argument("--agent", action="store_true", help="Run in agent mode to manage MCP services")

    args = p.parse_args(argv)
    
    if(args.agent):
        run_server()
        return 0
    
if __name__ == "__main__":
    raise SystemExit(main())


# xml_string = "<root><child>data</child></root>"
# root_element = ET.fromstring(xml_string)
# tree = TreeNode.from_xml(root_element)
# Now 'tree' is a TreeNode instance representing the XML structure
