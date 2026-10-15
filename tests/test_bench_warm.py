"""HIT/MISS classification uses server evidence, never request order."""

import importlib.util
from pathlib import Path


def load_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "find/outputs/company-packets/perf-staging-measurement/measure_load.py"
    )
    spec = importlib.util.spec_from_file_location("measure_load", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cache_class_follows_server_state_not_attempt_order():
    module = load_module()
    assert module.classify_cache("HIT") == "HIT"
    assert module.classify_cache("MISS") == "MISS"
    # A first attempt that hits a pre-warmed cache is still a HIT; an
    # evicted later attempt is still a MISS. Missing/odd states are UNKNOWN.
    assert module.classify_cache(None) == "UNKNOWN"
    assert module.classify_cache("STALE") == "UNKNOWN"
    assert module.classify_cache("") == "UNKNOWN"


def test_summary_groups_by_evidence_not_attempt():
    module = load_module()
    rows = [
        {"ticker": "AAPL", "attempt": 1, "wall_seconds": 2.8, "cache_class": "HIT"},
        {"ticker": "MSFT", "attempt": 1, "wall_seconds": 7.2, "cache_class": "MISS"},
        {"ticker": "AAPL", "attempt": 2, "wall_seconds": 1.9, "cache_class": "HIT"},
    ]
    summary = module.summarize(rows)
    assert summary["HIT"]["n"] == 2
    assert summary["MISS"]["n"] == 1
    assert summary["HIT"]["p50"] == 2.8
