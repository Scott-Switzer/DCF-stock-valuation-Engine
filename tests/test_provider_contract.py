import importlib
import pytest


def test_missing_values_cannot_become_zero():
    module = importlib.import_module("dcf_loader")
    assert hasattr(module, "parse_document"), (
        "A normalized, validated provider boundary is required."
    )
    from dcf_loader import parse_document, demo_document

    d = demo_document()
    del d["historical"][0]["capex"]
    with pytest.raises(ValueError, match="capex"):
        parse_document(d)


def test_demo_document_is_explicitly_synthetic_and_valid():
    module = importlib.import_module("dcf_loader")
    assert hasattr(module, "demo_document"), "Offline example data is required."
    doc = module.demo_document()
    data = module.parse_document(doc)
    assert doc["source"]["kind"] == "synthetic"
    assert data.metadata["is_demo"] is True
    data.validate()


def test_currency_mismatch_is_rejected():
    module = importlib.import_module("dcf_loader")
    assert hasattr(module, "demo_document")
    d = module.demo_document()
    d["market"]["currency"] = "EUR"
    with pytest.raises(ValueError, match="currency"):
        module.parse_document(d)


def test_period_duplicates_are_rejected():
    module = importlib.import_module("dcf_loader")
    assert hasattr(module, "demo_document")
    d = module.demo_document()
    d["historical"][1]["period_end"] = d["historical"][0]["period_end"]
    with pytest.raises(ValueError, match="period"):
        module.parse_document(d)


def test_unsupported_sector_is_rejected_server_side():
    module = importlib.import_module("dcf_loader")
    assert hasattr(module, "demo_document")
    d = module.demo_document()
    d["company"]["sector"] = "Banks"
    with pytest.raises(ValueError, match="model"):
        module.parse_document(d)
