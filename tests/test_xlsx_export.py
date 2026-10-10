"""Live-model XLSX exports: valid packages, all-formula calcs, sane endpoints."""

import io
import re
import zipfile
from dataclasses import asdict
import xml.etree.ElementTree as ET

from xlsx_export import dcf_workbook, ddm_workbook, relative_workbook
from dcf_loader import demo_document
from dcf_code import DCFAssumptions
from suite_models import (
    suite_sample,
    DDMAssumptions,
    RelativeAssumptions,
)
from suite_views import suite_evaluate
from app import app, evaluate

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def dcf_fixture():
    doc = demo_document()
    a = DCFAssumptions(
        revenue_growth_rates=[0.05] * 5,
        terminal_growth_rate=0.02,
        wacc_override=0.065,
        terminal_mode="template",
        ebit_margins=[0.25] * 5,
        da_margins=[0.05] * 5,
        capex_margins=[0.06] * 5,
        nwc_margins=[0.02] * 5,
        tax_rates=[0.21] * 5,
        net_income_margins=[0.18] * 5,
        book_value_margins=[0.5] * 5,
    )
    return doc, a, evaluate(doc, a)


def cells(wb_bytes):
    z = zipfile.ZipFile(io.BytesIO(wb_bytes))
    assert z.testzip() is None
    out = {}
    for name in z.namelist():
        if name.startswith("xl/worksheets/"):
            root = ET.fromstring(z.read(name))
            found = []
            for c in root.iter(NS + "c"):
                f = c.find(NS + "f")
                v = c.find(NS + "v")
                found.append((c.get("r"), f.text if f is not None else None,
                              v.text if v is not None else None))
            out[name] = found
    return out


def test_dcf_workbook_all_calculations_are_formulas():
    doc, a, r = dcf_fixture()
    sheets = cells(dcf_workbook(doc, asdict(a), r))
    assert len(sheets) == 7
    formulas = [f for cells_ in sheets.values() for _, f, _ in cells_ if f]
    assert len(formulas) > 100
    for addr, expr, _ in [c for cells_ in sheets.values() for c in cells_]:
        if expr and re.search(r"(?<![A-Z$])[0-9]{4,}", expr):
            raise AssertionError(f"hardcoded value in formula {addr}: {expr[:70]}")


def test_dcf_model_links_inputs():
    doc, a, r = dcf_fixture()
    sheets = cells(dcf_workbook(doc, asdict(a), r))
    model = sheets["xl/worksheets/sheet4.xml"]
    by_addr = {addr: expr for addr, expr, _ in model if expr}
    assert "Assumptions!" in by_addr["B2"]
    assert "Historical!" in by_addr["B9"]
    assert "B23/B24" in by_addr["B25"]


def test_ddm_and_relative_workbooks():
    dd = suite_sample("ddm")
    da = DDMAssumptions(
        dividend_growth_rates=[0.05] * 5,
        required_return=0.07,
        terminal_growth_rate=0.02,
    )
    ddm = cells(ddm_workbook(dd, asdict(da), suite_evaluate("ddm", dd, da)))
    assert len(ddm) == 7
    rc = suite_sample("relative")
    ca = RelativeAssumptions(included_methods=["ev_revenue", "ev_ebitda", "pe"])
    rel = cells(relative_workbook(rc, asdict(ca), suite_evaluate("relative", rc, ca)))
    assert len(rel) == 6
    model = rel["xl/worksheets/sheet4.xml"]
    exprs = [e for _, e, _ in model if e]
    assert any("SUMIF" in e for e in exprs)
    assert any("AVERAGE" in e for e in exprs)


def test_export_endpoints_serve_xlsx():
    doc, a, _ = dcf_fixture()
    client = app.test_client()
    payload = {"financials": doc, "assumptions": asdict(a)}
    for url in ["/export/xlsx", "/export/json"]:
        response = client.post(url, json=payload)
        assert response.status_code == 200, (url, response.get_json())
    xlsx = client.post("/export/xlsx", json=payload)
    assert "spreadsheetml.sheet" in xlsx.content_type
    assert zipfile.ZipFile(io.BytesIO(xlsx.data)).testzip() is None
    assert "attachment" in xlsx.headers["Content-Disposition"]
    assert xlsx.data[:2] == b"PK"


def test_relative_implied_price_formulas_are_well_formed():
    rc = suite_sample("relative")
    ca = RelativeAssumptions(included_methods=["ev_revenue", "ev_ebitda", "pe"])
    sheets = cells(relative_workbook(rc, asdict(ca), suite_evaluate("relative", rc, ca)))
    model = sheets["xl/worksheets/sheet4.xml"]
    prices = [
        e for addr, e, _ in model
        if e and addr[0] == "D" and addr[1:].isdigit() and 2 <= int(addr[1:]) <= 6
    ]
    assert len(prices) == 5
    for expr in prices:
        # A nested "=" inside a function call is an invalid Excel formula.
        assert not re.search(r"[(,]=", expr), expr


def test_suite_export_xlsx():
    client = app.test_client()
    dd = suite_sample("ddm")
    da = DDMAssumptions(
        dividend_growth_rates=[0.05] * 5,
        required_return=0.07,
        terminal_growth_rate=0.02,
    )
    response = client.post(
        "/export/ddm/xlsx",
        json={"financials": dd, "assumptions": asdict(da)},
    )
    assert response.status_code == 200, response.get_json()
    assert "spreadsheetml.sheet" in response.content_type
