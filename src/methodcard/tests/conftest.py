import sys
from pathlib import Path

DATA = Path(__file__).parent / "data"

# the toy package of methods, importable like an installed one
if str(DATA) not in sys.path:
    sys.path.insert(0, str(DATA))
