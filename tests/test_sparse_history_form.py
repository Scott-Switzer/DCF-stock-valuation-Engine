import pytest
from app import default_form
from dcf_loader import demo_document


@pytest.mark.parametrize("periods", [1, 2])
def test_partial_history_form_preserves_observed_margin(periods):
    doc = demo_document()
    doc["historical"] = doc["historical"][-periods:]
    for row in doc["historical"]:
        row["ebit"] = row["revenue"] * 0.2
        row["capex"] = None
    form = default_form(doc)
    assert form["ebit_margin_0"] == pytest.approx(20)
    assert form["capex_margin_0"] is None
    assert len(__import__("json").loads(form["base_document"])["historical"]) == periods
