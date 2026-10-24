"""Every registered strategy ships a valid ``step.toml`` that agrees with its code and config."""

import copy
import json
import re
import sys
import tomllib
from pathlib import Path

import pytest
from honba.strategies.base import Parameter
from honba.strategies.indicators import indicator_spec, list_indicators

from tools.mini_schema import validate
from tools.validate_chain import (
    KIND_ORDER,
    load_schema,
    load_step,
    schema_errors,
    value_errors,
)

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

ENTRIES = json.loads((ROOT / "registry.json").read_text())["strategies"]
IDS = [e["name"] for e in ENTRIES]
REF = re.compile(r"^\$([a-z][a-z0-9_]*)$")
# Parameter() defaults in strategy.py that differ from the shipped config.toml: (code, config).
# The manifest follows config.toml (what the strategy runs with). Fix the code or the config and
# this entry must go too; the test fails on a stale entry.
CODE_DEFAULT_MISMATCHES = {"sma_crossover": {"fast": (10, 20), "slow": (30, 50)}}


def _step(e):
    return load_step(ROOT / e["path"] / "step.toml")


def _config_values(e) -> dict:
    """Flat config values: ``[params]`` plus the args of each ``[indicators.*]`` table."""
    cfg = tomllib.loads((ROOT / e["path"] / "config.toml").read_text())
    flat = dict(cfg.get("params", {}))
    for table in cfg.get("indicators", {}).values():
        flat.update({k: v for k, v in table.items() if k != "kind"})
    return flat


@pytest.mark.parametrize("e", ENTRIES, ids=IDS)
def test_step_toml_exists_and_matches_schema(e):
    path = ROOT / e["path"] / "step.toml"
    assert path.is_file(), f"{e['path']}/step.toml missing"
    assert schema_errors(load_step(path)) == []


def test_no_step_toml_without_a_registered_strategy():
    registered = {e["path"] for e in ENTRIES}
    found = {p.parent.relative_to(ROOT).as_posix() for p in ROOT.rglob("step.toml")}
    assert found <= registered


@pytest.mark.parametrize("e", ENTRIES, ids=IDS)
def test_id_is_kind_dot_registry_name(e):
    s = _step(e)
    assert s["kind"] in KIND_ORDER
    assert s["id"] == f"{s['kind']}.{e['name']}"


@pytest.mark.parametrize("e", ENTRIES, ids=IDS)
def test_param_defaults_and_bounds(e):
    for name, p in _step(e)["params"].items():
        if p.get("optional"):
            continue
        assert value_errors(p, p["default"]) == [], (
            f"{name}: default outside its own spec"
        )
        if "min" in p and "max" in p:
            assert p["min"] <= p["max"], name
        if p["type"] == "enum":
            assert p["default"] in p["choices"], name
        assert "choices" not in p or p["type"] == "enum", (
            f"{name}: choices only for enum"
        )


@pytest.mark.parametrize("e", ENTRIES, ids=IDS)
def test_indicators_exist_and_bind_to_params(e):
    s = _step(e)
    known = set(list_indicators())
    aliases = []
    for ind in s["requires"]["indicators"]:
        assert ind["kind"] in known, f"unknown indicator {ind['kind']!r}"
        accepted = {p["name"] for p in indicator_spec(ind["kind"])["params"]}
        args = {k: v for k, v in ind.items() if k not in ("kind", "as")}
        assert set(args) <= accepted, (
            f"{ind['kind']}: {set(args) - accepted} not accepted"
        )
        for v in args.values():
            m = REF.match(v) if isinstance(v, str) else None
            if m:
                assert m.group(1) in s["params"], f"{ind['kind']}: {v} is not a param"
        aliases.append(ind.get("as"))
    named = [a for a in aliases if a]
    assert len(named) == len(set(named)), "indicator aliases must be unique"
    hist = s["requires"].get("history_bars")
    if isinstance(hist, str):
        ref = REF.match(hist)
        assert ref and s["params"][ref.group(1)]["type"] == "int"


@pytest.mark.parametrize("e", ENTRIES, ids=IDS)
def test_params_agree_with_config_toml(e):
    s, cfg = _step(e), _config_values(e)
    declared = s["params"]
    assert set(cfg) <= set(declared), (
        f"config keys without a manifest param: {set(cfg) - set(declared)}"
    )
    extra = set(declared) - set(cfg)
    assert all(declared[k].get("optional") for k in extra), (
        f"manifest params absent from config.toml must be optional: {sorted(extra)}"
    )
    for k, v in cfg.items():
        assert declared[k]["default"] == v, (
            f"{k}: manifest {declared[k]['default']!r} != config {v!r}"
        )


@pytest.mark.parametrize("e", ENTRIES, ids=IDS)
def test_params_agree_with_parameter_declarations(e, load_strategy):
    s = _step(e)
    mod = load_strategy(ROOT / e["path"])
    declared = {
        n: p
        for cls in vars(mod).values()
        if isinstance(cls, type)
        for n, p in vars(cls).items()
        if isinstance(p, Parameter)
    }
    mismatches = {}
    for name, p in declared.items():
        assert name in s["params"], f"Parameter {name!r} missing from step.toml"
        m = s["params"][name]
        assert (m.get("min"), m.get("max"), m.get("step")) == (p.min, p.max, p.step), (
            name
        )
        if m["default"] != p.default:
            mismatches[name] = (p.default, m["default"])
    assert mismatches == CODE_DEFAULT_MISMATCHES.get(e["name"], {})


# --- the validator itself must reject bad manifests ---------------------------------------


def _good():
    return _step(next(e for e in ENTRIES if e["name"] == "twap"))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: s.pop("requires"),
        lambda s: s.update(schema=2),
        lambda s: s.update(id="Signal.x"),
        lambda s: s.update(kind="buy"),
        lambda s: s.update(extra=1),
        lambda s: s["consumes"].update(shape="rows"),
        lambda s: s["params"]["total_quantity"].pop("description"),
        lambda s: s["params"]["total_quantity"].update(type="enum"),  # enum without choices
        lambda s: s["params"]["total_quantity"].update(default="ten"),
        lambda s: s["params"]["total_quantity"].pop("default"),
        lambda s: s["requires"]["indicators"].append({"period": 3}),
        lambda s: s["requires"].update(bars=["close", "close"]),
    ],
)
def test_schema_rejects_bad_manifest(mutate):
    s = copy.deepcopy(_good())
    mutate(s)
    assert validate(s, load_schema()) != []


# No portfolio strategies in current registry
PORTFOLIO = set()


def test_no_registered_step_is_kind_size():
    # a sizer consumes candidates and emits weights; none of the catalog strategies is one
    assert [e["name"] for e in ENTRIES if _step(e)["kind"] == "size"] == []


def test_schema_accepts_list_or_string_consumes_shape():
    s = copy.deepcopy(_good())
    s["consumes"]["shape"] = ["weights", "universe"]
    assert schema_errors(s) == []
    s["consumes"]["shape"] = "universe"
    assert schema_errors(s) == []
    for bad in ([], ["rows"], ["universe", "universe"], 3):
        s["consumes"]["shape"] = bad
        assert schema_errors(s) != [], bad


def test_schema_pitfalls_are_optional_and_must_be_unique_strings():
    s = copy.deepcopy(_good())
    s.pop("pitfalls", None)
    assert schema_errors(s) == []
    s["pitfalls"] = ["Parameter sweeps overfit; validate walk-forward."]
    assert schema_errors(s) == []
    for bad in ("one string", [3], [""], ["a", "a"]):
        s["pitfalls"] = bad
        assert schema_errors(s) != [], bad
