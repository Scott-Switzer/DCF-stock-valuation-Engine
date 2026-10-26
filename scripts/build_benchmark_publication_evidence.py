"""Curate source-backed publication evidence for the local Damodaran releases.

Read-only against the preserved evidence stores and the immutable release
objects; writes one additive ``publication_evidence.json`` catalog beside the
releases (plus a review copy and a receipt in the worktree). Nothing inside a
release directory is modified.

Evidence rule (mirroring the reviewed PPE importer contract): ``published_at``
comes only from the provider's HTTP ``Last-Modified`` date of the exact source
bytes, bound to the preserved ``evidence_sha256``. Download time and stated
vintage are disclosed but never used for availability; releases without that
evidence keep ``published_at: null`` and stay fail-closed at every historical
cutoff instead of being backdated from a download time or a guessed year.

Run:  python3.12 scripts/build_benchmark_publication_evidence.py
"""

import argparse
import hashlib
import json
import sys
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from valuation_benchmarks import (  # noqa: E402
    AVAILABLE,
    EVIDENCE_VERSION,
    UNAVAILABLE,
    encoded,
    load_publication_evidence,
    validate_publication,
)


def workspace_root():
    """The checkout's parent workspace: the directory holding ``data/ddfi``."""
    for candidate in [ROOT, *ROOT.parents]:
        if (candidate / "data/ddfi/registry/pilot_ingest_report.json").exists():
            return candidate
    raise SystemExit("WORKSPACE_ROOT_NOT_FOUND")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def ingest_records(evidence_root):
    """Preserved download records with the provider's Last-Modified header."""
    report = json.loads((evidence_root / "registry/pilot_ingest_report.json").read_bytes())
    records = {}

    def walk(node):
        if isinstance(node, dict):
            if node.get("sha256") and node.get("last_modified_server") and node.get("evidence_path"):
                records[node["sha256"]] = node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(report)
    return records


def stated_dates(evidence_root):
    """Provider-stated vintage dates, recorded but never used for availability."""
    index = json.loads((evidence_root / "registry/assumption_releases/index.json").read_bytes())
    return {
        row["source_sha256"]: row.get("stated_publication_date")
        for row in index.get("releases", [])
        if row.get("source_sha256")
    }


def verify_release(release_dir):
    manifest = json.loads((release_dir / "manifest.json").read_bytes())
    release = manifest.pop("release_id")
    if digest(encoded(manifest)) != release or release_dir.name != release:
        raise ValueError("RELEASE_IDENTITY_MISMATCH: " + release_dir.name)
    for name in ("source.bin", "normalized.json"):
        if digest((release_dir / name).read_bytes()) != manifest["files"][name]:
            raise ValueError("RELEASE_FILE_MISMATCH: " + release_dir.name + "/" + name)
    return release, manifest


def _same_retrieval(a, b):
    """True when two records describe the same download event.

    A date-only record is compared by day; it never implies an instant.
    """
    if len(str(a)) == 10 or len(str(b)) == 10:
        return date.fromisoformat(str(a)[:10]) == date.fromisoformat(str(b)[:10])
    return datetime.fromisoformat(str(a).replace("Z", "+00:00")) == datetime.fromisoformat(
        str(b).replace("Z", "+00:00")
    )


def retrieval_record(release_dir, manifest):
    """The release's recorded download time, with its real precision.

    ``retrieval.json`` wins when present; otherwise the manifest's
    ``lineage.retrieved_at`` is used. A date-only value keeps day precision and
    is never upgraded to an asserted instant. Two disagreeing records are a
    conflict, not a choice to make silently.
    """
    path = release_dir / "retrieval.json"
    from_file = json.loads(path.read_bytes()).get("retrieved_at") if path.exists() else None
    from_lineage = (manifest.get("lineage") or {}).get("retrieved_at")
    if from_file and from_lineage and not _same_retrieval(from_file, from_lineage):
        raise ValueError("RETRIEVAL_CONFLICT: " + release_dir.name)
    source = "retrieval.json" if from_file else "manifest.lineage.retrieved_at"
    values = [v for v in (from_file, from_lineage) if v]
    if not values:
        raise ValueError("RELEASE_RETRIEVAL_UNKNOWN: " + release_dir.name)
    # Keep the coarsest recorded value: a day already stated as a day is never
    # narrowed into an asserted instant.
    value = next((v for v in values if len(str(v)) == 10), values[0])
    precision = "day" if len(str(value)) == 10 else "instant"
    return {"value": value, "precision": precision, "source": source}


def build_entry(release, manifest, evidence_root, record, stated, retrieval):
    source_sha = manifest["files"]["source.bin"]
    retrieved_at = retrieval["value"]
    entry = {
        "release_id": release,
        "dataset_id": manifest["dataset_id"],
        "region": manifest["region"],
        "source_url": manifest["source_url"],
        "source_sha256": source_sha,
        "download_retrieved_at": retrieved_at,
        "download_retrieved_at_precision": retrieval["precision"],
        "download_retrieved_at_source": retrieval["source"],
        "stated_publication_date": stated,
        "stated_vintage_role": "DISCLOSED_NOT_USED_FOR_AVAILABILITY",
    }
    if record is None:
        entry.update(
            published_at=None,
            publication_evidence=None,
            historical_availability=UNAVAILABLE,
            unavailable_reason=(
                "no preserved publication evidence for these exact source bytes; "
                "download time and stated vintage are disclosed but never used for availability"
            ),
        )
        return entry

    raw = (evidence_root / record["evidence_path"]).read_bytes()
    if digest(raw) != record["sha256"] or digest(raw) != source_sha:
        raise ValueError("EVIDENCE_BYTES_NOT_BOUND_TO_RELEASE: " + release)
    modified = parsedate_to_datetime(record["last_modified_server"])
    observed_at = record["fetched_at"]
    evidence = {
        "method": "SERVER_LAST_MODIFIED",
        "source_url": manifest["source_url"],
        "server_last_modified": record["last_modified_server"],
        "observed_at": observed_at,
        "statement": (
            "HTTP Last-Modified of the exact source bytes, recorded at ingest and "
            "bound to evidence_sha256"
        ),
        "evidence_sha256": record["sha256"],
        "evidence_path": record["evidence_path"],
    }
    published = modified.date().isoformat()
    # The single validation contract shared with the loader rejects guessed or
    # download-time dates before anything is stored.
    validate_publication(published, evidence, observed_at)
    if date.fromisoformat(str(retrieved_at)[:10]) < modified.date():
        raise ValueError("PUBLICATION_AFTER_RELEASE_RETRIEVAL: " + release)
    entry.update(
        published_at=published,
        publication_evidence=evidence,
        historical_availability=AVAILABLE,
    )
    return entry


def main():
    parser = argparse.ArgumentParser()
    workspace = workspace_root()
    parser.add_argument(
        "--releases",
        type=Path,
        default=workspace / "artifacts/zero-subscription-integration/damodaran-releases",
    )
    parser.add_argument("--evidence-root", type=Path, default=workspace / "data/ddfi")
    args = parser.parse_args()

    evidence_root = args.evidence_root.resolve()
    records = ingest_records(evidence_root)
    stated = stated_dates(evidence_root)

    entries = []
    for release_dir in sorted(args.releases.iterdir()):
        if not release_dir.is_dir():
            continue
        release, manifest = verify_release(release_dir)
        source_sha = manifest["files"]["source.bin"]
        retrieval = retrieval_record(release_dir, manifest)
        entry = build_entry(
            release, manifest, evidence_root, records.get(source_sha), stated.get(source_sha), retrieval
        )
        entries.append(entry)
        print(
            json.dumps(
                {
                    "release": release[:12],
                    "dataset": entry["dataset_id"],
                    "published_at": entry["published_at"],
                    "availability": entry["historical_availability"],
                }
            ),
            flush=True,
        )

    catalog = {
        "schema_version": EVIDENCE_VERSION,
        "evidence_rule": (
            "published_at is the provider HTTP Last-Modified date of the exact source "
            "bytes bound to evidence_sha256; download time and stated vintage are "
            "disclosed but never used for availability"
        ),
        "curated_from": [
            "data/ddfi/registry/pilot_ingest_report.json (server Last-Modified records)",
            "data/ddfi/evidence/ (byte-identical preserved source bytes)",
        ],
        "releases": sorted(entries, key=lambda e: e["release_id"]),
    }
    body = json.dumps(catalog, indent=2, sort_keys=True).encode() + b"\n"

    catalog_path = args.releases / "publication_evidence.json"
    catalog_path.write_bytes(body)
    review_copy = ROOT / "evidence/benchmark_publication_evidence.json"
    review_copy.parent.mkdir(parents=True, exist_ok=True)
    review_copy.write_bytes(body)

    loaded = load_publication_evidence(args.releases)
    if set(loaded) != {entry["release_id"] for entry in entries}:
        raise ValueError("CATALOG_ROUNDTRIP_MISMATCH")
    receipt = {
        "status": "PREPARED_NOT_PROMOTED",
        "catalog_sha256": digest(body),
        "catalog_keys": [str(catalog_path), str(review_copy)],
        "releases_recorded": sum(1 for e in entries if e["published_at"]),
        "releases_fail_closed": sum(1 for e in entries if not e["published_at"]),
        "release_objects_modified": 0,
        "production_writes": 0,
        "entries": [
            {
                "release_id": e["release_id"],
                "dataset_id": e["dataset_id"],
                "published_at": e["published_at"],
                "source_sha256": e["source_sha256"],
                "evidence_sha256": (e["publication_evidence"] or {}).get("evidence_sha256"),
                "historical_availability": e["historical_availability"],
            }
            for e in entries
        ],
    }
    receipt_path = ROOT / "evidence/benchmark-publication-evidence-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "PASS", "receipt": str(receipt_path)}))


if __name__ == "__main__":
    main()
