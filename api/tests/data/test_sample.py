import re
import shutil
from datetime import date
from pathlib import Path

import yaml

from app.data.sample import write_sample

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "data"
DAY = date(2026, 11, 23)


def _data_dir(tmp_path: Path) -> Path:
    """Fixture data plus extra rules, so there are more than 10 rows to sample from."""
    dest = tmp_path / "data"
    shutil.copytree(FIXTURE, dest)
    rules = yaml.safe_load((dest / "rules.yaml").read_text())
    rules += [dict(rules[0], step_order=10 + i) for i in range(6)]
    (dest / "rules.yaml").write_text(yaml.safe_dump(rules, allow_unicode=True))
    return dest


def test_sample_is_deterministic_and_has_ten_sourced_entries(tmp_path: Path) -> None:
    data = _data_dir(tmp_path)
    first = write_sample(data, tmp_path / "a", seed=7, day=DAY)
    second = write_sample(data, tmp_path / "b", seed=7, day=DAY)

    assert first.name == "2026-11-23.md"
    text = first.read_text()
    assert text == second.read_text()

    entries = re.split(r"^## ", text, flags=re.M)[1:]
    assert len(entries) == 10
    for entry in entries:
        assert re.search(r"^- source_url: https?://\S+$", entry, flags=re.M)
        assert "verified by owner: yes/no, note:" in entry
