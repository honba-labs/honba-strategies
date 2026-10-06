"""registry.json is the index of the catalog; keep it consistent with the tree."""
import json
import re
from pathlib import Path

import pytest
from honba.strategies.indicators import FAMILIES

ROOT = Path(__file__).resolve().parent
ENTRIES = json.loads((ROOT / "registry.json").read_text())["strategies"]


@pytest.mark.parametrize("e", ENTRIES, ids=lambda e: e["name"])
def test_entry_is_consistent_with_tree(e):
    # path is <category>/<dir>; the name is the dir, or a prefixed form of it (alpha30_factor)
    leaf = e["path"].rsplit("/", 1)[-1]
    assert e["path"] == f'{e["category"]}/{leaf}'
    assert e["name"] == leaf or e["name"].endswith(f"_{leaf}")
    d = ROOT / e["path"]
    for f in ("strategy.py", "config.toml", "README.md", "tests/test_strategy.py"):
        assert (d / f).is_file(), f"{e['path']}/{f} missing"
    assert e["tags"] and set(e["tags"]) <= set(FAMILIES), f"tags must be indicator families: {FAMILIES}"


def test_names_are_unique():
    names = [e["name"] for e in ENTRIES]
    assert len(names) == len(set(names))


def test_directories_are_not_numbered():
    numbered = [p.name for p in ROOT.iterdir() if p.is_dir() and re.match(r"\d+_", p.name)]
    assert numbered == []
