import sys
from pathlib import Path

# Ensure the project root is on sys.path so that the implicit namespace package 'src' is importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# (Optional) also ensure the src directory itself is present (harmless if duplicate)
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.append(str(SRC))
