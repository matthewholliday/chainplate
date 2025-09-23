import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from .modes.chainplate_server import run_server


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