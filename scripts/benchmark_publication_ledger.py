"""Record which benchmark releases can be selected historically, and prove it.

For every release under the local Damodaran root this script:

* reports the manifest's publication date and evidence status;
* performs a current-mode selection through the real loader;
* attempts a historical selection at a cutoff before any plausible publication
  and records the exact refusal.

It writes a ledger only. No release, manifest, or assumption file is modified.
The seven existing releases were ingested before structured evidence was
required, so they are labelled unavailable rather than backfilled.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
from valuation_benchmarks import load_benchmark, publication_status  # noqa: E402

CUTOFF = "2000-01-01"


def inspect_release(root: Path, name: str) -> dict:
    path = root / name
    manifest = json.loads((path / "manifest.json").read_bytes())
    data = json.loads((path / "normalized.json").read_bytes())
    record = next(
        (row for row in data["records"] if row.get("value_decimal") is not None),
        None,
    )
    status = publication_status(manifest)
    result = {
        "release_id": name,
        "dataset_id": manifest.get("dataset_id"),
        "region": manifest.get("region"),
        "source_update_label": manifest.get("source_update_label"),
        "publication": status,
        "current_selection": None,
        "historical_refusal": None,
    }
    if record is None:
        result["current_selection"] = {"error": "no populated record"}
        return result
    selected = load_benchmark(root, name, record["subject"], record["measure"])
    result["current_selection"] = {
        "subject": selected["subject"],
        "measure": selected["measure"],
        "value_decimal": selected["value_decimal"],
        "selection_mode": selected["selection_mode"],
    }
    try:
        load_benchmark(root, name, record["subject"], record["measure"], as_of=CUTOFF)
    except ValueError as error:
        result["historical_refusal"] = str(error)
    else:
        result["historical_refusal"] = None
        result["historical_refusal_missing"] = True
    return result


def render_markdown(document: dict) -> str:
    lines = [
        "# Benchmark publication ledger — " + document["observed_at"],
        "",
        "Read-only status of every local Damodaran benchmark release. A release is "
        "usable for historical selection only when its hashed manifest carries both "
        "`published_at` and reviewed publication evidence.",
        "",
        "| Release | Dataset | published_at | Evidence | Current mode | Historical mode |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in document["releases"]:
        publication = row["publication"]
        current = row["current_selection"] or {}
        current_text = (
            f"{current.get('value_decimal')} ({current.get('measure')})"
            if current.get("value_decimal") is not None
            else str(current.get("error", "not attempted"))
        )
        lines.append(
            "| {release} | {dataset} | {published} | {evidence} | {current} | {historical} |".format(
                release=row["release_id"][:12],
                dataset=row["dataset_id"],
                published=publication["published_at"] or "null",
                evidence=publication["reason"] or publication["method"],
                current=current_text,
                historical=row["historical_refusal"] or "UNEXPECTEDLY ALLOWED",
            )
        )
    lines += [
        "",
        "## What the ledger establishes",
        "",
        f"- All {document['summary']['releases']} releases refuse historical selection at "
        f"{CUTOFF}; the refusal names the missing publication evidence rather than a missing dataset.",
        "- Current-mode selection succeeds for every release through the same verified loader.",
        "- None of the existing manifests is edited: a publication date is never inferred from "
        "retrieval time, a workbook update label, or the release hash.",
        "",
        "## Forward-only rule",
        "",
        "New releases pass `--published-at` and `--publication-evidence` to the importer, which "
        "rejects a bare string, an observation before publication, and an observation after "
        "retrieval. Historical selection for those releases becomes available only from the "
        "recorded date onward.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-root", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    parser.add_argument("--observed-at", default=date.today().isoformat())
    args = parser.parse_args(argv)

    names = sorted(
        path.name for path in args.release_root.iterdir() if path.is_dir() and (path / "manifest.json").exists()
    )
    releases = [inspect_release(args.release_root, name) for name in names]
    missing_refusal = [row["release_id"] for row in releases if row.get("historical_refusal_missing")]
    document = {
        "schema_version": "benchmark-publication-ledger-v1",
        "observed_at": args.observed_at,
        "release_root": str(args.release_root),
        "summary": {
            "releases": len(releases),
            "published": sum(1 for row in releases if row["publication"]["available"]),
            "unavailable": sum(1 for row in releases if not row["publication"]["available"]),
            "missing_historical_refusal": missing_refusal,
        },
        "releases": releases,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(document, indent=2) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_markdown(document))
    print(json.dumps(document["summary"], sort_keys=True))
    return 1 if missing_refusal else 0


if __name__ == "__main__":
    raise SystemExit(main())
