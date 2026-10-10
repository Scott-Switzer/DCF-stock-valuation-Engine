from unittest.mock import patch
from app import app
from dcf_loader import ProviderError


def test_company_packet_api_missing_and_failure(tmp_path):
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    with app.test_client() as client:
        with patch("ppe_provider.load_packet", return_value=None):
            assert client.get("/api/company/AAPL").status_code == 404
        with patch("ppe_provider.load_packet", side_effect=ProviderError("Integrity failure")):
            assert client.get("/api/company/AAPL").status_code == 503
        with patch(
            "ppe_provider.load_packet",
            return_value={"schema_version": "ppe-valuation-packet-v1", "ticker": "AAPL"},
        ):
            response = client.get("/api/company/AAPL")
            assert response.status_code == 200
            assert response.headers["Cache-Control"] == (
                "public, max-age=300, stale-while-revalidate=600"
            )


def test_loading_fallback_is_explicit(tmp_path):
    from auto_loading import load_method
    from dcf_loader import demo_document

    d = demo_document()
    d["company"]["ticker"] = "AAPL"
    d["valuation_date"] = "2026-10-07"
    d["source"]["common_dividends"] = {"historical": [], "value": 1, "period_end": "2025-12-31"}
    d["source"]["capital_costs"] = {}
    with (
        patch("auto_loading.load_yahoo", return_value=d),
        patch("ppe_provider.load_packet", side_effect=ProviderError("Packet unavailable")),
        patch("auto_loading.company_classification", return_value=None),
        patch("auto_loading.recalculate_costs", return_value={}),
    ):
        loaded = load_method("dcf", "AAPL", "2026-10-07")
    assert loaded["financials"]["source"]["ppe_status"] == "Packet unavailable"
    assert any("PPE packet unavailable" in x for x in loaded["financials"]["source"]["warnings"])


def test_cache_hits_do_not_extend_pointer_lifetime(monkeypatch):
    import sys
    from types import SimpleNamespace
    import ppe_provider

    cache = SimpleNamespace(match=lambda req: SimpleNamespace(text=lambda: '{"cached":true}'))
    writes = []
    cache.put = lambda *args: writes.append(args)
    monkeypatch.setitem(
        sys.modules, "pyodide.ffi", SimpleNamespace(run_sync=lambda x: x, to_js=lambda x, **kw: x)
    )
    monkeypatch.setitem(
        sys.modules,
        "js",
        SimpleNamespace(
            Object=SimpleNamespace(fromEntries=None),
            Request=SimpleNamespace(new=lambda x: x),
            Response=SimpleNamespace(new=lambda *args: args),
            caches=SimpleNamespace(default=cache),
        ),
    )
    bucket = SimpleNamespace(
        get=lambda key: (_ for _ in ()).throw(AssertionError("Unexpected R2 read"))
    )
    assert ppe_provider._object_json(bucket, ppe_provider.POINTER, maximum=100) == {"cached": True}
    assert writes == []


def test_cache_failure_uses_authoritative_r2_and_rejects_bad_hash(monkeypatch):
    import sys
    from types import SimpleNamespace
    import ppe_provider

    cache = SimpleNamespace(
        match=lambda req: (_ for _ in ()).throw(RuntimeError("Cache unavailable")),
        put=lambda *args: None,
    )
    monkeypatch.setitem(
        sys.modules, "pyodide.ffi", SimpleNamespace(run_sync=lambda x: x, to_js=lambda x, **kw: x)
    )
    monkeypatch.setitem(
        sys.modules,
        "js",
        SimpleNamespace(
            Object=SimpleNamespace(fromEntries=None),
            Request=SimpleNamespace(new=lambda x: x),
            Response=SimpleNamespace(new=lambda *args: args),
            caches=SimpleNamespace(default=cache),
        ),
    )
    bucket = SimpleNamespace(get=lambda key: SimpleNamespace(size=2, text=lambda: "{}"))
    assert ppe_provider._object_json(bucket, "key", maximum=100) == {}
    with __import__("pytest").raises(ProviderError, match="integrity"):
        ppe_provider._object_json(bucket, "key", maximum=100, digest="a" * 64)


def test_body_read_failure_is_a_provider_error(monkeypatch):
    import sys
    from types import SimpleNamespace
    from ppe_provider import _object_json

    monkeypatch.setitem(
        sys.modules, "pyodide.ffi", SimpleNamespace(run_sync=lambda x: x, to_js=lambda x, **kw: x)
    )
    monkeypatch.setitem(
        sys.modules, "js", SimpleNamespace(Object=SimpleNamespace(fromEntries=None))
    )
    obj = SimpleNamespace(size=2, text=lambda: (_ for _ in ()).throw(RuntimeError("body failed")))
    with __import__("pytest").raises(ProviderError, match="body"):
        _object_json(SimpleNamespace(get=lambda key: obj), "key", maximum=100)


def test_incompatible_merged_model_uses_baseline_instead_of_500():
    from copy import deepcopy
    from dcf_loader import demo_document
    from ppe_provider import prefer_ppe

    baseline = demo_document()
    candidate = deepcopy(baseline)
    candidate["historical"][-1]["tax_rate"] = 2
    with (
        patch("ppe_provider.load_packet", return_value={"published": True}),
        patch("ppe_packets.apply_packet", return_value=candidate),
    ):
        result = prefer_ppe(baseline, "DEMO", baseline["valuation_date"])
    assert result["historical"][-1]["tax_rate"] == baseline["historical"][-1]["tax_rate"]
    assert "input requirements" in result["source"]["ppe_status"]


def test_slow_ppe_promise_is_bounded_by_shared_deadline(monkeypatch):
    import asyncio
    import sys
    import time
    from types import SimpleNamespace
    from ppe_provider import _wait

    monkeypatch.setitem(sys.modules, 'pyodide.ffi', SimpleNamespace(run_sync=asyncio.run))
    async def slow():
        await asyncio.sleep(5)
    start = time.monotonic()
    with __import__('pytest').raises(ProviderError, match='shared request deadline'):
        _wait(slow(), start + 0.02)
    assert time.monotonic() - start < 0.5


def test_ppe_pointer_and_body_receive_same_deadline(monkeypatch):
    from types import SimpleNamespace
    import ppe_provider
    calls = []
    monkeypatch.setattr(ppe_provider, '_object_json', lambda bucket, key, **kw: calls.append(kw['deadline']))
    with app.test_request_context('/', environ_overrides={'workers.env': SimpleNamespace(PPE_DATA=object())}):
        monkeypatch.setitem(app.config, 'CLOUDFLARE', True)
        assert ppe_provider.load_packet('AAPL', '2026-10-10', deadline=123.0) is None
    assert calls == [123.0]
