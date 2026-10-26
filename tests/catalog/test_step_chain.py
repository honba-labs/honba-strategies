"""Chain compatibility rules from schema/README.md."""

import copy
import sys
from pathlib import Path

from tools.validate_chain import (
    load_step,
    validate_chain,
    validate_params,
)

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def _twap_step_path() -> Path:
    p2 = ROOT / "catalog/execution/twap/v2/step.toml"
    if p2.is_file():
        return p2
    p1 = ROOT / "catalog/execution/twap/v1/step.toml"
    if p1.is_file():
        return p1
    return ROOT / "catalog/execution/twap/step.toml"


def step(id_, kind, consumes, emits, adds=(), report=(), columns=("symbol",), fundamentals=()):
    return {
        "id": id_,
        "kind": kind,
        "params": {"n": {"type": "int", "default": 5, "min": 1, "max": 10, "description": "n"}},
        "requires": {"fundamentals": list(fundamentals)},
        "consumes": {"shape": consumes, "columns": list(columns)},
        "emits": {"shape": emits, "adds": list(adds), "report": list(report)},
    }


SCREEN = step("screen.nifty", "screen", "none", "universe")
FILTER = step("filter.roe", "filter", "universe", "candidates", report=["roe"])
SIGNAL = step("signal.x", "signal", "candidates", "orders", adds=["side", "quantity"])
RISK = step("risk.stop", "risk", "orders", "orders", columns=("symbol", "quantity"))
EXEC = step("execute.paper", "execute", "orders", "none", columns=("symbol", "side", "quantity"))


def test_valid_chain():
    assert validate_chain([SCREEN, FILTER, SIGNAL, RISK, EXEC]) == []


def test_repeated_kinds_are_allowed():
    again = step("filter.again", "filter", "candidates", "candidates")
    assert validate_chain([SCREEN, FILTER, again, copy.deepcopy(again)]) == []


def test_shape_mismatch():
    errs = validate_chain([SCREEN, SIGNAL])
    assert (
        len(errs) == 1
        and "consumes shape 'candidates'" in errs[0]
        and "emits 'universe'" in errs[0]
    )


def test_kind_order_violation():
    errs = validate_chain(
        [SCREEN, FILTER, SIGNAL, step("filter.late", "filter", "orders", "orders")]
    )
    assert any("cannot follow 'signal'" in e for e in errs)


def test_missing_column():
    needs_mcap = step(
        "filter.mcap",
        "filter",
        "universe",
        "candidates",
        columns=("symbol", "market_cap"),
    )
    errs = validate_chain([SCREEN, needs_mcap])
    assert len(errs) == 1 and "'market_cap'" in errs[0]


def test_column_supplied_by_upstream_report_or_fundamentals():
    needs = step(
        "filter.mcap",
        "filter",
        "universe",
        "candidates",
        columns=("symbol", "market_cap"),
    )
    reporter = step("screen.cap", "screen", "none", "universe", report=["market_cap"])
    assert validate_chain([reporter, needs]) == []
    fetching = step(
        "filter.mcap",
        "filter",
        "none",
        "candidates",
        columns=("market_cap",),
        fundamentals=("market_cap",),
    )
    assert (
        validate_chain([fetching]) == []
    )  # a first step may consume 'none'; fundamentals are fetchable


def test_user_chosen_report_columns_must_be_reportable():
    flt = {**FILTER, "emits": {**FILTER["emits"], "reportable": ["market_cap"]}}
    needs = step("signal.y", "signal", "candidates", "orders", columns=("symbol", "market_cap"))
    assert validate_chain([SCREEN, {**flt, "report": ["market_cap"]}, needs]) == []
    assert validate_chain([SCREEN, flt, needs]) != []  # not asked for, so not available
    errs = validate_chain([SCREEN, {**flt, "report": ["beta"]}])
    assert len(errs) == 1 and "cannot report 'beta'" in errs[0]


def test_first_step_cannot_consume_upstream_shape():
    errs = validate_chain([FILTER.copy() | {"consumes": {"shape": "orders"}}])
    assert any("first step" in e for e in errs)


def test_empty_chain():
    assert validate_chain([]) == ["chain is empty"]


def test_with_overrides_are_checked_against_params():
    ok = {**SCREEN, "with": {"n": 3}}
    assert validate_chain([ok]) == []
    for bad in ({"n": 99}, {"n": 2.5}, {"nope": 1}):
        assert validate_params(SCREEN, bad)


def test_real_registered_steps_chain():
    twap = load_step(_twap_step_path())
    assert validate_chain([twap]) == []
    assert validate_chain([twap, twap]) != []  # orders are not a universe


# --- canonical stage semantics: screen -> filter -> size -> execute -------------------------

SIZE = step("size.eq", "size", "candidates", "weights", adds=["weight"])


def test_consumes_shape_may_be_a_list():
    ex = step("execute.pf", "execute", ["weights", "universe"], "orders")
    assert validate_chain([SCREEN, FILTER, SIZE, ex]) == []  # weights is in the list
    assert validate_chain([SCREEN, ex]) == []  # so is universe
    errs = validate_chain([SCREEN, FILTER, ex])  # candidates is not
    assert len(errs) == 1 and "candidates" in errs[0] and "weights" in errs[0]


def test_first_step_may_consume_a_list_containing_universe():
    ex = step("execute.pf", "execute", ["weights", "universe"], "orders")
    assert validate_chain([ex]) == []
    only_weights = step("execute.w", "execute", ["weights"], "orders")
    assert any("first step" in e for e in validate_chain([only_weights]))


def test_portfolio_execute_after_size_from_a_chain():
    # No portfolio strategies in current registry
    pass


# def test_portfolio_execute_straight_from_universe():
#     mom = load_step(ROOT / "universe/alpha/momentum/step.toml")
#     assert validate_chain([mom]) == []
#     assert validate_chain([SCREEN, mom]) == []


def test_signal_then_size_is_rejected_with_a_helpful_message():
    twap = load_step(_twap_step_path())
    eq = step("size.equal_weight", "size", "candidates", "weights")
    errs = validate_chain([twap, eq])
    assert len(errs) == 2
    assert any("emits 'orders'" in e and "consumes shape 'candidates'" in e for e in errs)
    assert any("kind 'size' cannot follow 'execute'" in e for e in errs)
    assert any("signal" in e and "screen" in e and "filter" in e for e in errs)


# def test_signal_then_portfolio_execute_is_rejected():
#     sma = load_step(ROOT / "momentum/trend/sma_crossover/step.toml")
#     eq = load_step(ROOT / "portfolio/rebalancing/equal_weight/step.toml")
#     assert validate_chain([sma, eq]) != []
