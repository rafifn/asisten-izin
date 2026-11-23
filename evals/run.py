"""Run the eval set: `make eval` (dry by default), `make eval EVAL_ARGS=--yes` (real API, paid)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app.evals.runner import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
