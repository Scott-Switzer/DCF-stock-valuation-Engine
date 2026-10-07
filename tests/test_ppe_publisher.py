import json
import pytest
from dcf_loader import ProviderError
from scripts import publish_ppe_packets as publisher


def test_failed_publisher_preserves_diagnostics_without_ready_companies(tmp_path, monkeypatch):
    class BrokenR2:
        def __init__(self, config):
            pass

        def get(self, *args):
            raise ProviderError("Immutable artifact hash mismatch.")

        def close(self):
            pass

    report = tmp_path / "nested" / "failed.json"
    monkeypatch.setattr(publisher, "R2", BrokenR2)
    monkeypatch.setattr(
        "sys.argv", ["publisher", "--config", "fixture", "--report", str(report), "--publish"]
    )
    with pytest.raises(ProviderError):
        publisher.main()
    saved = json.loads(report.read_text())
    assert saved["published"] is False
    assert saved["companies"] == []
    assert saved["failure"] == "Immutable artifact hash mismatch."


def test_failure_preserves_exclusions_after_last_checkpoint(tmp_path, monkeypatch):
    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    identities = [
        {"symbol": s, "artifact_path": f"entities/entity_sec_cik_{i:010d}"}
        for i, s in enumerate(symbols, 1)
    ]
    manifest = {
        "serving_release_id": "a" * 32,
        "artifacts": [
            {"path": "identity/resolver_index.json", "storage_key": "resolver", "sha256": "b" * 64},
            {
                "path": identities[-1]["artifact_path"] + "/fundamentals/annual.json",
                "storage_key": "failed-annual",
                "sha256": "c" * 64,
            },
        ],
    }

    class R2WithLaterFailure:
        def __init__(self, config):
            pass

        def get(self, key, *args):
            return {
                "gold/serving/coverage25/CURRENT.json": {
                    "manifest_key": "manifest",
                    "manifest_sha256": "a" * 64,
                },
                "manifest": manifest,
                "resolver": identities,
            }[key]

        def call(self, op, **kwargs):
            if kwargs["items"]:
                raise ProviderError("Remote annual artifact unavailable.")
            return []

        def close(self):
            pass

    report = tmp_path / "failed.json"
    monkeypatch.setattr(publisher, "R2", R2WithLaterFailure)
    monkeypatch.setattr(
        "sys.argv",
        ["publisher", "--config", "fixture", "--report", str(report), "--all", "--publish"],
    )
    with pytest.raises(ProviderError):
        publisher.main()
    saved = json.loads(report.read_text())
    assert saved["published"] is False
    assert [x["ticker"] for x in saved["companies"]] == symbols[:4]
    assert all(x["status"] == "NO_ANNUAL_ARTIFACT" for x in saved["companies"])
