"""Chain validation for step manifests (see ``schema/README.md`` for the rules).

``validate_chain`` takes the step manifests (parsed ``step.toml`` dicts, in run order) and
returns a list of human-readable errors; an empty list means the chain is compatible. A step
may carry an optional ``"with"`` mapping of param overrides, which is checked against the
step's declared params (the GitHub Actions ``with:`` idea), and an optional ``"report"`` list of
extra columns to report, which must be among the step's ``emits.reportable``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import tomllib

from tools.mini_schema import validate

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schema" / "step.schema.json"
KIND_ORDER = ("screen", "filter", "signal", "size", "risk", "execute")
# What nothing-before-it can hand a first step: a starting universe, or nothing at all.
FIRST_SHAPES = ("universe", "none")
BASE_COLUMNS = frozenset({"symbol"})  # every universe row has a symbol


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def load_step(path: Path) -> dict:
    return tomllib.loads(Path(path).read_text())


def schema_errors(step: dict) -> list[str]:
    """Errors from validating one manifest against ``step.schema.json``."""
    return validate(step, load_schema())


def validate_params(step: dict, values: dict[str, Any]) -> list[str]:
    """Check param ``values`` against the step's declared type, bounds, choices and pattern."""
    errs: list[str] = []
    declared = step.get("params", {})
    for name, value in values.items():
        spec = declared.get(name)
        if spec is None:
            errs.append(f"{step.get('id')}: unknown param {name!r}")
            continue
        errs += [f"{step.get('id')}.{name}: {e}" for e in value_errors(spec, value)]
    return errs


def value_errors(spec: dict, value: Any) -> list[str]:
    """Why ``value`` is not acceptable for a param ``spec`` (empty when it is)."""
    kind = spec["type"]
    if kind == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            return [f"{value!r} is not an int"]
    elif kind == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return [f"{value!r} is not a number"]
    elif kind == "bool":
        if not isinstance(value, bool):
            return [f"{value!r} is not a bool"]
    elif kind == "symbols":
        if not isinstance(value, (str, list)):
            return [f"{value!r} is not a universe name or list of symbols"]
        return []
    elif not isinstance(value, str):
        return [f"{value!r} is not a string"]
    errs = []
    if kind in ("int", "float"):
        if "min" in spec and value < spec["min"]:
            errs.append(f"{value} below min {spec['min']}")
        if "max" in spec and value > spec["max"]:
            errs.append(f"{value} above max {spec['max']}")
    if kind == "enum" and value not in spec.get("choices", []):
        errs.append(f"{value!r} not in {spec.get('choices')}")
    if (
        "pattern" in spec
        and isinstance(value, str)
        and not re.fullmatch(spec["pattern"], value)
    ):
        errs.append(f"{value!r} does not match {spec['pattern']!r}")
    return errs


def validate_chain(steps: list[dict]) -> list[str]:
    """Errors for running ``steps`` in order; an empty list means the chain is valid."""
    errs: list[str] = []
    if not steps:
        return ["chain is empty"]
    available = set(BASE_COLUMNS)
    prev: dict | None = None
    prev_rank = -1
    for i, step in enumerate(steps):
        sid = step.get("id", f"#{i}")
        kind = step.get("kind")
        if kind not in KIND_ORDER:
            errs.append(f"{sid}: unknown kind {kind!r}")
            rank = prev_rank
        else:
            rank = KIND_ORDER.index(kind)
            if rank < prev_rank:
                errs.append(
                    f"{sid}: kind '{kind}' cannot follow '{KIND_ORDER[prev_rank]}' "
                    f"(order is {' -> '.join(KIND_ORDER)})"
                )
        consumes = step.get("consumes", {})
        shape = consumes.get("shape")
        if prev is None:
            if shape not in FIRST_SHAPES:
                errs.append(
                    f"{sid}: first step must consume one of {FIRST_SHAPES}, not {shape!r}"
                )
        else:
            produced = prev.get("emits", {}).get("shape")
            if produced != shape:
                errs.append(
                    f"{sid}: consumes shape {shape!r} but {prev.get('id')} emits {produced!r}"
                )
        fetchable = set(step.get("requires", {}).get("fundamentals", []))
        for col in consumes.get("columns", []):
            if col not in available and col not in fetchable:
                errs.append(
                    f"{sid}: needs column {col!r}, which no earlier step adds or reports "
                    f"and is not in its requires.fundamentals"
                )
        errs += validate_params(step, step.get("with", {}))
        emits = step.get("emits", {})
        asked = set(
            step.get("report", [])
        )  # extra columns the user asked this step to report
        allowed = set(emits.get("reportable", [])) | set(emits.get("report", []))
        for col in sorted(asked - allowed):
            errs.append(
                f"{sid}: cannot report {col!r}; reportable columns are {sorted(allowed)}"
            )
        available |= (
            set(emits.get("adds", []))
            | set(emits.get("report", []))
            | (asked & allowed)
        )
        prev, prev_rank = step, max(rank, prev_rank)
    return errs
