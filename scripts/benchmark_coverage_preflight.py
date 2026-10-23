"""Read-only benchmark coverage preflight for the local Damodaran releases.

Verifies, without writing to the release store, that:

1. the publication-evidence catalog is byte-bound to each release's exact source
   bytes and the root and review copies are identical;
2. every release's subject/measure coverage is enumerable (the app can list
   available pairs instead of failing at selection);
3. historical cutoffs before supported availability stay fail-closed: evidenced
   releases serve on and after their source-backed ``published_at`` and refuse
   before it, and releases without publication evidence refuse every historical
   cutoff while current-mode selection stays unchanged.

Writes only its own report artifacts. Run:
  python3.12 scripts/benchmark_coverage_preflight.py
"""

import argparse
import hashlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from valuation_benchmarks import (  # noqa: E402
    AVAILABLE,
    coverage_catalog,
    load_benchmark,
    load_publication_evidence,
)

OUT = Path(__file__).resolve().parents[3] / "artifacts/path1-benchmark-vintage"


def workspace_root():
    for candidate in [ROOT, *ROOT.parents]:
        if (candidate / "data/ddfi/registry/pilot_ingest_report.json").exists():
            return candidate
    raise SystemExit("WORKSPACE_ROOT_NOT_FOUND")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def probe(root, entry, subject, measure):
    """Exercise the loader's historical gates for one subject/measure pair."""
    result = {}
    served = load_benchmark(root, entry["release_id"], subject, measure)
    result["current_mode"] = {
        "served": True,
        "published_at": served["published_at"],
        "selection_mode": served["selection_mode"],
        "historical_availability": served["historical_availability"],
    }
    if entry["published_at"]:
        published = date.fromisoformat(entry["published_at"])
        before = (published - timedelta(days=1)).isoformat()
        on = published.isoformat()
        try:
            load_benchmark(root, entry["release_id"], subject, measure, as_of=before)
            result["day_before_published"] = {"refused": False}
        except ValueError as error:
            result["day_before_published"] = {"refused": True, "reason": str(error)}
        historical = load_benchmark(root, entry["release_id"], subject, measure, as_of=on)
        result["published_day"] = {
            "served": True,
            "published_at": historical["published_at"],
            "selection_mode": historical["selection_mode"],
            "value_decimal": historical["value_decimal"],
        }
    else:
        refusals = {}
        for cutoff in ("2020-01-01", "2026-10-14", "2026-12-31"):
            try:
                load_benchmark(root, entry["release_id"], subject, measure, as_of=cutoff)
                refusals[cutoff] = {"refused": False}
            except ValueError as error:
                refusals[cutoff] = {"refused": True, "reason": str(error)}
        result["historical_cutoffs"] = refusals
    return result


def main():
    parser = argparse.ArgumentParser()
    workspace = workspace_root()
    parser.add_argument(
        "--releases",
        type=Path,
        default=workspace / "artifacts/zero-subscription-integration/damodaran-releases",
    )
    args = parser.parse_args()
    root = args.releases
    checks = []
    failures = []

    def check(name, condition, detail):
        checks.append({"check": name, "pass": bool(condition), "detail": detail})
        if not condition:
            failures.append(name)

    catalog = load_publication_evidence(root)
    review_copy = ROOT / "evidence/benchmark_publication_evidence.json"
    check(
        "catalog_copies_identical",
        review_copy.read_bytes() == (root / "publication_evidence.json").read_bytes(),
        [str(root / "publication_evidence.json"), str(review_copy)],
    )

    listing = coverage_catalog(root)
    rows = []
    for entry in listing:
        release_dir = root / entry["release_id"]
        source_sha = digest((release_dir / "source.bin").read_bytes())
        catalog_entry = catalog.get(entry["release_id"]) or {}
        check(
            "catalog_byte_bound:" + entry["dataset_id"],
            catalog_entry.get("source_sha256") == source_sha,
            {"source_sha256": source_sha},
        )
        if entry["historical_availability"] == AVAILABLE:
            check(
                "evidence_dates_from_server_header:" + entry["dataset_id"],
                bool(entry["published_at"])
                and bool((entry["publication_evidence"] or {}).get("server_last_modified")),
                {"published_at": entry["published_at"]},
            )
        else:
            check(
                "fail_closed_without_evidence:" + entry["dataset_id"],
                entry["published_at"] is None and entry["publication_evidence"] is None,
                {"historical_availability": entry["historical_availability"]},
            )
        pair = entry["subject_measure_pairs"][0]
        probed = probe(root, entry, pair["subject"], pair["measure"])
        if entry["published_at"]:
            check(
                "historical_refused_before_publication:" + entry["dataset_id"],
                probed["day_before_published"]["refused"],
                probed["day_before_published"],
            )
            check(
                "historical_served_on_publication:" + entry["dataset_id"],
                probed["published_day"]["served"]
                and probed["published_day"]["selection_mode"] == "HISTORICAL_PUBLISHED"
                and probed["published_day"]["published_at"] == entry["published_at"],
                probed["published_day"],
            )
        else:
            check(
                "historical_fail_closed:" + entry["dataset_id"],
                all(v["refused"] for v in probed["historical_cutoffs"].values()),
                probed["historical_cutoffs"],
            )
        check(
            "current_mode_unchanged:" + entry["dataset_id"],
            probed["current_mode"]["served"]
            and probed["current_mode"]["selection_mode"] == "CURRENT_EXPLICIT_SELECTION",
            probed["current_mode"],
        )
        rows.append({**entry, "probe": probed})

    report = {
        "status": "PASS" if not failures else "FAIL",
        "read_only": True,
        "release_store_writes": 0,
        "releases": rows,
        "checks": checks,
        "failures": failures,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "coverage-preflight.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Benchmark coverage preflight (read-only)",
        "",
        f"Status: {report['status']}",
        "",
        "| dataset | subjects | target measures | published_at | availability |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {dataset} | {subjects} | {targets} | {published} | {availability} |".format(
                dataset=row["dataset_id"],
                subjects=row["subjects"],
                targets=", ".join(row["target_measures_available"]) or "-",
                published=row["published_at"] or "-",
                availability=row["historical_availability"],
            )
        )
    lines += [
        "",
        "published_at is the provider HTTP Last-Modified date of the exact source",
        "bytes bound to evidence_sha256. Download time and stated vintage are",
        "disclosed but never used for availability: releases without that evidence",
        "stay fail-closed at every historical cutoff.",
        "",
    ]
    (OUT / "coverage-preflight.md").write_text("\n".join(lines))
    print(json.dumps({"status": report["status"], "checks": len(checks), "failures": failures}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
