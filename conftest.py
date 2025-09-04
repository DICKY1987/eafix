import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
# Ensure the project root is on ``sys.path`` so that local packages such as
# ``jsonschema`` can be imported.  Append rather than insert to avoid shadowing
# test modules with identical names in nested directories.
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
