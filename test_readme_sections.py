"""Every registered strategy README must teach usage, show output and warn about pitfalls."""

import json
import re
from pathlib import Path

import pytest
import tomllib

ROOT = Path(__file__).resolve().parent
ENTRIES = json.loads((ROOT / "registry.json").read_text())["strategies"]

# Rollout in chunks: chunk A covered the 11 single-instrument strategies; chunk B must cover the
# portfolio ones and then EMPTY this set, so the rule applies to all registered strategies.
PENDING_README_SECTIONS = {
    "alpha30_factor",
    "alpha30_low_vol",
    "alpha30_mean_reversion",
    "alpha30_momentum",
    "alpha30_quality",
    "equal_weight",
}
# READMES_REQUIRED = all registered except PENDING_README_SECTIONS
READMES_REQUIRED = [e for e in ENTRIES if e["name"] not in PENDING_README_SECTIONS]
REQUIRED_HEADINGS = ("## Usage", "## Possible output", "## Pitfalls")
MIN_LINES = 3
MIN_PITFALLS = 3
BACKTEST_BIASES_URL = (
    "https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html"
)


def _sections(text: str) -> dict[str, list[str]]:
    """Level-2 heading -> its body lines (up to the next level-2 heading, fences respected)."""
    out: dict[str, list[str]] = {}
    current = None
    fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and re.match(r"## \S", line):
            current = line.rstrip()
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return out


IDS = [e["name"] for e in READMES_REQUIRED]


def test_pending_names_are_registered():
    assert PENDING_README_SECTIONS <= {e["name"] for e in ENTRIES}


@pytest.mark.parametrize("e", READMES_REQUIRED, ids=IDS)
def test_readme_has_required_sections(e):
    sections = _sections((ROOT / e["path"] / "README.md").read_text())
    for heading in REQUIRED_HEADINGS:
        assert heading in sections, f"{e['name']}: README lacks '{heading}'"
        body = [ln for ln in sections[heading] if ln.strip()]
        assert len(body) >= MIN_LINES, f"{e['name']}: '{heading}' is too short"


@pytest.mark.parametrize("e", READMES_REQUIRED, ids=IDS)
def test_pitfalls_have_bullets_and_link_the_bias_page(e):
    text = (ROOT / e["path"] / "README.md").read_text()
    pitfalls = _sections(text).get("## Pitfalls", [])
    bullets = [ln for ln in pitfalls if re.match(r"\s*[-*] \S", ln)]
    assert len(bullets) >= MIN_PITFALLS, f"{e['name']}: needs >= {MIN_PITFALLS} bullets"
    assert BACKTEST_BIASES_URL in "\n".join(pitfalls), (
        f"{e['name']}: Pitfalls must link {BACKTEST_BIASES_URL}"
    )


@pytest.mark.parametrize("e", READMES_REQUIRED, ids=IDS)
def test_step_toml_pitfalls_are_short_strings(e):
    step = tomllib.loads((ROOT / e["path"] / "step.toml").read_text())
    pitfalls = step.get("pitfalls")
    assert isinstance(pitfalls, list) and 2 <= len(pitfalls) <= 4, e["name"]
    assert all(isinstance(p, str) and 10 <= len(p) <= 160 for p in pitfalls)
