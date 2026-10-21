"""registry.json is the index of the catalog; keep it consistent with the tree."""

import ast
import json
import re
import tomllib
from pathlib import Path

import pytest
from honba.strategies.indicators import FAMILIES

ROOT = Path(__file__).resolve().parent
ENTRIES = json.loads((ROOT / "registry.json").read_text())["strategies"]
# The loader reads only name/path; everything else is catalog metadata. No extra keys.
ALLOWED_KEYS = {"name", "category", "path", "description", "tags"}
SCAFFOLD_STATUS = "scaffold"


def _is_trivial(strategy_py: Path) -> bool:
    """True when the module is empty or only a docstring (a scaffold)."""
    body = ast.parse(strategy_py.read_text()).body
    return all(
        isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Constant)
        and isinstance(n.value.value, str)
        for n in body
    )


def _strategy_dirs():
    return sorted(
        p.parent
        for p in ROOT.rglob("strategy.py")
        if not any(part.startswith(".") for part in p.relative_to(ROOT).parts)
    )


def _config(d: Path) -> dict:
    return tomllib.loads((d / "config.toml").read_text())


REGISTERED = {e["path"] for e in ENTRIES}
SCAFFOLDS = [d for d in _strategy_dirs() if _is_trivial(d / "strategy.py")]
REAL = [d for d in _strategy_dirs() if d not in SCAFFOLDS]


@pytest.mark.parametrize("e", ENTRIES, ids=lambda e: e["name"])
def test_entry_is_consistent_with_tree(e):
    # path is <category>/<dir>; the name is the dir, or a prefixed form of it (alpha30_factor)
    leaf = e["path"].rsplit("/", 1)[-1]
    assert e["path"] == f"{e['category']}/{leaf}"
    assert e["name"] == leaf or e["name"].endswith(f"_{leaf}")
    d = ROOT / e["path"]
    for f in ("strategy.py", "config.toml", "README.md", "tests/test_strategy.py"):
        assert (d / f).is_file(), f"{e['path']}/{f} missing"
    assert e["tags"] and set(e["tags"]) <= set(FAMILIES), (
        f"tags must be indicator families: {FAMILIES}"
    )


def test_names_are_unique():
    names = [e["name"] for e in ENTRIES]
    assert len(names) == len(set(names))


def test_directories_are_not_numbered():
    numbered = [
        p.name for p in ROOT.iterdir() if p.is_dir() and re.match(r"\d+_", p.name)
    ]
    assert numbered == []


@pytest.mark.parametrize("e", ENTRIES, ids=lambda e: e["name"])
def test_entry_keys_and_category(e):
    assert set(e) == ALLOWED_KEYS, (
        f"{e['name']}: keys must be exactly {sorted(ALLOWED_KEYS)}"
    )
    assert isinstance(e["description"], str) and e["description"].strip()
    assert (ROOT / e["category"]).is_dir()
    assert e["path"].startswith(e["category"] + "/")


@pytest.mark.parametrize("d", REAL, ids=lambda d: str(d.relative_to(ROOT)))
def test_real_strategy_is_registered(d):
    rel = d.relative_to(ROOT).as_posix()
    assert rel in REGISTERED, (
        f"{rel} has a real strategy.py but is not in registry.json"
    )
    assert _config(d).get("status") != SCAFFOLD_STATUS, (
        f"{rel} is real but marked scaffold"
    )


@pytest.mark.parametrize("d", SCAFFOLDS, ids=lambda d: str(d.relative_to(ROOT)))
def test_scaffold_is_marked_and_unregistered(d):
    rel = d.relative_to(ROOT).as_posix()
    assert _config(d).get("status") == SCAFFOLD_STATUS, (
        f'{rel}: docstring-only strategy.py needs status = "scaffold" in config.toml'
    )
    assert rel not in REGISTERED, f"{rel} is a scaffold and must not be registered"


def test_scaffold_marker_only_on_trivial_strategies():
    marked = {
        d for d in _strategy_dirs() if _config(d).get("status") == SCAFFOLD_STATUS
    }
    assert marked == set(SCAFFOLDS)


def test_registered_paths_are_strategy_dirs():
    assert REGISTERED <= {d.relative_to(ROOT).as_posix() for d in REAL}
