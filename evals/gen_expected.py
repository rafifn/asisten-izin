"""Regenerate expected permits/risk in cases.yaml from the rules engine (see `make eval-gen`)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app.evals.expected import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
