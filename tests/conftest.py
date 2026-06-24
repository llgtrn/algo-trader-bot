import sys
from pathlib import Path

# Put the repo root on sys.path so `daemon` and `brain` import cleanly.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
