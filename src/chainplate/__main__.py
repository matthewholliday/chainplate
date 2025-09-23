import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from .modes.chainplate_server import run_server


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="chainplate",
        description="Agentic AI framework for building and managing custom AI applications.",
    )
    p.add_argument("--agent", action="store_true", help="Run in agent mode to manage MCP services")

    args = p.parse_args(argv)
    
    if(args.agent):
        run_server()
        return 0
    # No arguments supplied: present a friendly default message instead of silently exiting
    # Keep exit code 0 so that simple install verification (just running `chainplate`) succeeds.
    default_message = (
        "Chainplate CLI\n"
        "No arguments provided.\n\n"
        "Examples:\n"
        "  chainplate --agent        Start agent mode to manage MCP services.\n"
        "  chainplate --help         Show full help and available options.\n\n"
        "Project: https://github.com/matthewholliday/chainplate\n"
    )
    print(default_message, file=sys.stderr)
    return 0
    
if __name__ == "__main__":
    raise SystemExit(main())