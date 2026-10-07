"""Templates, history, share links and watchlist use caller-scoped storage."""

import pytest

from app import app


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "library.sqlite3"))


def client(tmp_path):
    app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))
    return app.test_client()


ASSUMPTIONS = {
    "revenue_growth_rates": [0.05] * 5,
    "terminal_growth_rate": 0.02,
    "wacc_override": 0.065,
    "terminal_mode": "template",
    "ebit_margins": [0.2] * 5,
    "da_margins": [0.05] * 5,
    "capex_margins": [0.06] * 5,
    "nwc_margins": [0.02] * 5,
    "tax_rates": [0.21] * 5,
    "net_income_margins": [0.15] * 5,
    "book_value_margins": [0.5] * 5,
}


def test_templates_crud(tmp_path):
    c = client(tmp_path)
    assert c.get("/api/templates?method=dcf").get_json() == []
    saved = c.post(
        "/api/templates",
        json={"name": "Bull", "method": "dcf", "assumptions": ASSUMPTIONS},
    )
    assert saved.status_code == 200
    listed = c.get("/api/templates?method=dcf").get_json()
    assert len(listed) == 1 and listed[0]["assumptions"] == ASSUMPTIONS
    assert c.get("/api/templates?method=ddm").get_json() == []
    assert c.delete(f"/api/templates/{listed[0]['id']}").status_code == 200
    assert c.get("/api/templates").get_json() == []
    bad = c.post("/api/templates", json={"name": "", "method": "dcf",
                                          "assumptions": ASSUMPTIONS})
    assert bad.status_code == 400


def test_cookie_identity_persists_across_days(tmp_path):
    c = client(tmp_path)
    c.post(
        "/api/templates",
        json={"name": "Keep", "method": "dcf", "assumptions": ASSUMPTIONS},
    )
    cookie = c.get_cookie("lib_id")
    assert cookie is not None
    # A second client presenting the same cookie sees the same library.
    other = app.test_client()
    other.set_cookie("lib_id", cookie.value)
    names = [t["name"] for t in other.get("/api/templates").get_json()]
    assert names == ["Keep"]
    # A tampered cookie is rejected and mints a fresh, empty scope.
    forged = app.test_client()
    forged.set_cookie("lib_id", cookie.value[:-2] + "xx")
    assert forged.get("/api/templates").get_json() == []


def test_share_requires_owned_valuation(tmp_path):
    c = client(tmp_path)
    missing = c.post("/api/share", json={"valuation_id": "nope"})
    assert missing.status_code == 400
    assert c.get("/v/nope").status_code == 404


def test_watchlist_crud_and_validation(tmp_path):
    c = client(tmp_path)
    assert c.get("/api/watchlist").get_json() == []
    assert c.post("/api/watchlist",
                  json={"ticker": "AAPL", "target": 200, "direction": "above"}
                  ).status_code == 200
    assert c.post("/api/watchlist",
                  json={"ticker": "!!!", "target": 1, "direction": "above"}
                  ).status_code == 400
    assert c.post("/api/watchlist",
                  json={"ticker": "AAPL", "target": 1, "direction": "sideways"}
                  ).status_code == 400
    entries = c.get("/api/watchlist").get_json()
    assert [e["ticker"] for e in entries] == ["AAPL"]
    assert c.delete("/api/watchlist", json={"ticker": "AAPL"}).status_code == 200
    assert c.get("/api/watchlist").get_json() == []


def test_history_empty_without_saves(tmp_path):
    c = client(tmp_path)
    assert c.get("/api/history?ticker=AAPL").get_json() == []


def test_shared_view_renders_saved_record(tmp_path):
    import library
    from dcf_loader import demo_document
    from dcf_code import DCFAssumptions

    c = client(tmp_path)
    doc = demo_document()
    a = DCFAssumptions(**ASSUMPTIONS)
    from app import evaluate

    result = evaluate(doc, a)
    from valuation_records import record_values

    c.get("/api/history")  # mints the signed owner cookie
    cookie = c.get_cookie("lib_id")
    assert cookie is not None
    with app.test_request_context(
        "/",
        environ_overrides={
            "REMOTE_ADDR": "127.0.0.1",
            "HTTP_COOKIE": f"lib_id={cookie.value}",
        },
    ):
        values = record_values(doc, a, result, library.caller_hash())
        library.history()
    import sqlite3
    from storage import Store

    db = sqlite3.connect(Store().path)
    with db:
        db.execute(
            "INSERT OR IGNORE INTO valuations(method,id,created_at,model_version,"
            "ticker,valuation_date,source_kind,is_demo,intrinsic_value,"
            "target_price_12m,market_price,upside,assumptions_json,financials_json,"
            "result_json,client_hash,input_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            values,
        )
    db.close()
    # Find the record through history, then share and view it.
    rows = c.get("/api/history").get_json()
    assert len(rows) == 1
    token = c.post("/api/share", json={"valuation_id": rows[0]["id"]}).get_json()["token"]
    page = c.get(f"/v/{token}")
    assert page.status_code == 200
    assert b"Shared read-only" in page.data


@pytest.mark.parametrize("proxied", [True, False])
def test_workers_library_reads_d1_result_envelope(tmp_path, monkeypatch, proxied):
    import sys
    from types import ModuleType, SimpleNamespace
    import library

    class Results:
        def to_py(self):
            return [{"id": "fixture", "name": "Bull"}]

    class Statement:
        def bind(self, *params):
            assert params == ("owner",)
            return self

        def all(self):
            return SimpleNamespace(results=Results() if proxied else [{"id": "fixture", "name": "Bull"}], success=True)

    ffi = ModuleType("pyodide.ffi")
    ffi.run_sync = lambda value: value
    monkeypatch.setitem(sys.modules, "pyodide.ffi", ffi)
    db = SimpleNamespace(prepare=lambda sql: Statement())
    monkeypatch.setitem(app.config, "CLOUDFLARE", True)
    with app.test_request_context("/api/templates", environ_overrides={"workers.env": SimpleNamespace(DB=db)}):
        assert library._fetchall("SELECT id,name FROM templates WHERE client_hash=?", ("owner",)) == [{"id": "fixture", "name": "Bull"}]


def test_workers_cookie_signing_uses_request_secret(monkeypatch):
    from types import SimpleNamespace
    import library
    monkeypatch.setitem(app.config, "CLOUDFLARE", True)
    monkeypatch.delenv("LIBRARY_SECRET", raising=False)
    with app.test_request_context("/api/templates", environ_overrides={"workers.env": SimpleNamespace(LIBRARY_SECRET="fixture-server-secret")}):
        assert library._secret() == b"fixture-server-secret"


def test_first_calculation_mints_library_identity(tmp_path):
    import library
    with app.test_request_context("/api/calculate"):
        library.ensure_identity()
        assert library.caller_hash().startswith("lib:")


def test_worker_saved_valuation_uses_library_owner(monkeypatch):
    import sys
    from types import ModuleType, SimpleNamespace
    import library
    from valuation_records import save_valuation
    from app import assumptions_from_json, evaluate
    from dcf_loader import demo_document
    values = []

    class Statement:
        def bind(self, *args):
            values.append(args)
            return self

        def run(self):
            return None

        def first(self):
            return SimpleNamespace(id="saved-fixture")

    ffi = ModuleType("pyodide.ffi")
    ffi.run_sync = lambda value: value
    monkeypatch.setitem(sys.modules, "pyodide.ffi", ffi)
    monkeypatch.setitem(app.config, "CLOUDFLARE", True)
    env = SimpleNamespace(DB=SimpleNamespace(prepare=lambda sql: Statement()))
    doc=demo_document()
    a=assumptions_from_json(ASSUMPTIONS)
    with app.test_request_context("/api/calculate", environ_overrides={"workers.env": env, "dcf.client_hash": "daily-network", "lib.new_identity": "persistent-browser"}):
        assert save_valuation(doc,a,evaluate(doc,a)) == "saved-fixture"
        assert values[0][-2] == library.caller_hash() == "lib:persistent-browser"


def test_workers_cookie_secret_derives_from_private_binding(monkeypatch):
    from types import SimpleNamespace
    import library
    monkeypatch.setitem(app.config, "CLOUDFLARE", True)
    with app.test_request_context("/api/templates", environ_overrides={"workers.env": SimpleNamespace(RECORD_SALT="fixture-private-key")}):
        assert len(library._secret()) == 32
        assert library._secret() != b"dev-only-library-secret"
    with app.test_request_context("/api/templates", environ_overrides={"workers.env": SimpleNamespace()}):
        with pytest.raises(RuntimeError, match="production library signing secret"):
            library._secret()
