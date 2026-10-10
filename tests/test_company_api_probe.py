"""The company API probe reports coverage and never echoes secrets."""

import importlib.util
import json
from pathlib import Path

import pytest
import requests

from dcf_loader import ProviderError

SPEC = importlib.util.spec_from_file_location(
    "check_company_api", Path(__file__).resolve().parents[1] / "scripts/check_company_api.py"
)
probe_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe_module)

ASOF = "2026-10-06"
SECRET = "secret-token-value-123"


def observation(metric, year, value, unit="USD"):
    return {"metric_id": metric, "period_type": "annual", "period_end": f"{year}-12-31",
            "available_at": f"{year + 1}-02-01T00:00:00Z", "unit": unit,
            "value_decimal": value}


def packet(symbol="AAPL", extra=()):
    annual = [observation("revenue", y, v) for y, v in [(2023, "100"), (2024, "120"), (2025, "150")]]
    return {"symbol": symbol, "status": "AVAILABLE", "request_id": "r1", "releases": {},
            "identity": {}, "prices": {},
            "fundamentals": {"status": "AVAILABLE", "annual": annual + list(extra)}}


def test_summary_reports_periods_and_unmapped_metrics():
    summary = probe_module.summarize(
        packet(extra=[observation("goodwill", 2025, "5")]), "AAPL", ASOF)
    assert summary["periods"] == ["2023-12-31", "2024-12-31", "2025-12-31"]
    assert summary["unmapped_metric_ids"] == ["goodwill"]
    assert "ebit" in summary["blank_history_fields"]
    assert summary["price_mapped"] is False


def test_mismatched_symbol_is_a_contract_violation():
    with pytest.raises(ProviderError):
        probe_module.summarize(packet("MSFT"), "AAPL", ASOF)


def test_probe_requires_an_https_base(monkeypatch, capsys):
    monkeypatch.setenv("ZION_API_BASE_URL", "http://insecure.example")
    assert probe_module.probe(["probe", "AAPL", ASOF]) == 2
    assert "HTTPS" in capsys.readouterr().err


def test_probe_success_prints_coverage_without_token(monkeypatch, capsys):
    monkeypatch.setenv("ZION_API_BASE_URL", "https://company-api.example")
    monkeypatch.setenv("ZION_API_TOKEN", SECRET)
    seen = {}

    class Response:
        status_code = 200
        content = b"{}"

        def json(self):
            return packet()

    def fake_get(url, headers, params, timeout, allow_redirects):
        seen.update(headers=headers, params=params, allow_redirects=allow_redirects)
        return Response()

    monkeypatch.setattr(requests, "get", fake_get)
    assert probe_module.probe(["probe", "aapl", ASOF]) == 0
    out = capsys.readouterr().out
    assert SECRET not in out and "company-api.example" not in out
    assert json.loads(out)["periods"][-1] == "2025-12-31"
    assert seen["headers"] == {"Authorization": f"Bearer {SECRET}"}
    assert seen["params"]["as_of"] == f"{ASOF}T23:59:59Z"
    assert seen["allow_redirects"] is False


def test_probe_failure_never_echoes_the_error_body(monkeypatch, capsys):
    monkeypatch.setenv("ZION_API_BASE_URL", "https://company-api.example")
    monkeypatch.setenv("ZION_API_TOKEN", SECRET)

    def boom(*args, **kwargs):
        raise requests.ConnectionError(f"failed contacting company-api.example with {SECRET}")

    monkeypatch.setattr(requests, "get", boom)
    assert probe_module.probe(["probe", "AAPL", ASOF]) == 1
    err = capsys.readouterr().err
    assert SECRET not in err and "company-api.example" not in err
