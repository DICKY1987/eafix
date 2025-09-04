import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# Ensure the src directory is on ``sys.path`` so that the ``eafix`` package can
# be imported during testing. Append rather than insert to avoid shadowing test
# modules with identical names in nested directories.
if str(SRC) not in sys.path:
    sys.path.append(str(SRC))
