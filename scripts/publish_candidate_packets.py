"""Candidate-only staging packet publication; production pointers are read-only.

Builds validated PPE packets from published fundamentals plus an SEC
companyfacts supplement and stages them under an isolated candidate index
selected by PPE_POINTER_OVERRIDE (default: control/valuation/CANDIDATE-staging.json).

Safety properties (enforced in code, not documentation):
- The production pointer control/valuation/CURRENT.json is NEVER written:
  CandidateTransport refuses the write, and --pointer rejects it at startup.
- Before/after SHA-256 digests of the raw production pointer bytes are
  recorded to prove it is byte-identical; canonical-JSON digests are kept
  alongside as an explicitly labeled semantic comparison only.
- Packet artifacts are immutable and content-addressed; uploads are
  conditional (If-None-Match *) with read-back digest verification.
- The candidate pointer update is conditional on its original ETag and
  preserves every existing entry (e.g. PEP); the previous pointer content
  is recorded for rollback, with --restore-pointer to apply it.
- Dry-run is the default; nothing is written without --publish.
"""

import argparse
import base64
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dcf_loader import ProviderError, ticker_symbol
from ppe_packets import build_packet
from scripts.ppe_cloud_source import CandidateTransport, SecArchive, rclone_client


def symbol_entries(value):
    if isinstance(value, dict):
        if value.get("symbol") and value.get("artifact_path"):
            yield value
        for v in value.values():
            yield from symbol_entries(v)
    elif isinstance(value, list):
        for v in value:
            yield from symbol_entries(v)


def canonical(raw: bytes):
    return json.dumps(json.loads(raw), sort_keys=True, separators=(",", ":")).encode()


def digest(data: bytes):
    return hashlib.sha256(data).hexdigest()


def pointer_integrity(raw):
    """(raw_sha256, canonical_sha256) for a pointer object, or (None, None).

    Byte identity is the raw digest; the canonical digest is a semantic
    comparison only and must never substitute for raw-byte identity.
    """
    if raw is None:
        return None, None
    try:
        canonical_sha = digest(canonical(raw))
    except (TypeError, ValueError):
        canonical_sha = None
    return digest(raw), canonical_sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rclone-remote", required=True)
    parser.add_argument("--sec-archive-key", required=True)
    parser.add_argument("--sec-archive-bucket", default="financial-data-wrds-private")
    parser.add_argument("--symbols", default="CAT")
    parser.add_argument("--pointer", default=CandidateTransport.DEFAULT_POINTER)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--restore-pointer", default=None,
                        help="Local rollback file holding previous pointer JSON; restores it conditionally.")
    parser.add_argument("--rollback-out", default=None,
                        help="Where to record the previous pointer content for rollback.")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    if args.pointer == CandidateTransport.PRODUCTION_POINTER:
        raise ProviderError("Refusing to treat the production pointer as a candidate index.")
    transport = CandidateTransport(rclone_client(args.rclone_remote), pointer=args.pointer)
    archive = SecArchive(transport.client, args.sec_archive_bucket, args.sec_archive_key)
    cutoff = datetime.now(timezone.utc).date().isoformat()
    report = {"cutoff_date": cutoff, "pointer": args.pointer,
              "published": False, "companies": []}
    try:
        if args.restore_pointer:
            if not args.publish:
                raise ProviderError("--restore-pointer requires --publish (dry-run restores nothing).")
            prior = transport.call("get", args.pointer)
            if prior is None:
                raise ProviderError("No candidate pointer to restore against.")
            # call() does not record ETags; the conditional restore needs it.
            transport.etags[args.pointer] = prior["etag"]
            raw = Path(args.restore_pointer).read_bytes()
            transport.call("put", args.pointer, raw,
                           expected_etag=transport.etags.get(args.pointer))
            report["published"] = True
            report["restored_from"] = args.restore_pointer
            Path(args.report).parent.mkdir(parents=True, exist_ok=True)
            Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps({"restored": args.pointer}))
            return

        serving = transport.get("gold/serving/coverage25/CURRENT.json")
        manifest = transport.get(serving["manifest_key"], serving["manifest_sha256"])
        base = "gold/serving/releases/" + manifest["serving_release_id"] + "/"
        entries = {x["path"]: x for x in manifest["artifacts"]}

        def artifact(path):
            entry = entries[path]
            return transport.get(entry.get("storage_key", base + path), entry["sha256"])

        index = artifact("identity/resolver_index.json")
        resolved = {}
        for entry in symbol_entries(index):
            try:
                symbol = ticker_symbol(entry["symbol"])
            except ValueError:
                continue
            resolved.setdefault(symbol, entry)

        # Production pointer integrity, before: the raw-byte digest is the
        # byte-identity proof; the canonical digest is a semantic comparison
        # only and must never substitute for raw identity.
        prod_before = transport.call("get", CandidateTransport.PRODUCTION_POINTER)
        raw_sha, canonical_sha = pointer_integrity(
            base64.b64decode(prod_before["body"]) if prod_before else None)
        report["production_pointer_sha256_before"] = raw_sha
        report["production_pointer_canonical_sha256_before"] = canonical_sha

        prior_raw = None
        prior_entry = transport.call("get", args.pointer)
        if prior_entry is not None:
            # call() does not record ETags; the conditional pointer update needs it.
            transport.etags[args.pointer] = prior_entry["etag"]
            prior_raw = base64.b64decode(prior_entry["body"])
            prior_index = json.loads(prior_raw)
            if (not isinstance(prior_index, dict)
                    or prior_index.get("schema_version") != "ppe-valuation-index-v1"
                    or not isinstance(prior_index.get("companies"), dict)):
                raise ProviderError("Existing candidate index schema mismatch; refusing to merge.")
            prior_companies = dict(prior_index["companies"])
        else:
            prior_companies = {}
        report["candidate_pointer_sha256_before"] = digest(prior_raw) if prior_raw else None
        report["candidate_companies_before"] = sorted(prior_companies)
        if args.rollback_out and prior_raw is not None:
            Path(args.rollback_out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.rollback_out).write_bytes(prior_raw)
            report["rollback_file"] = args.rollback_out

        packet_index = {}
        for ticker in [ticker_symbol(x) for x in args.symbols.split(",")]:
            if ticker not in resolved:
                report["companies"].append({"ticker": ticker, "status": "NOT_IN_RESOLVER"})
                continue
            entity = resolved[ticker]
            issuer = re.search(r"entity_sec_cik_([0-9]{10})(?:_[A-Z-]+)?$",
                               entity.get("artifact_path", ""))
            if not issuer:
                raise ProviderError("Unsupported SEC issuer path.")
            cik = issuer.group(1)
            path = entity["artifact_path"] + "/fundamentals/annual.json"
            entry = entries.get(path)
            if not entry:
                report["companies"].append({"ticker": ticker, "status": "NO_ANNUAL_ARTIFACT"})
                continue
            rows = artifact(path)
            rows = rows if isinstance(rows, list) else rows.get("rows", [])
            try:
                facts, provenance = archive.facts(cik)
            except (ProviderError, ValueError) as exc:
                report["companies"].append(
                    {"ticker": ticker, "status": "SEC_SUPPLEMENT_REJECTED", "reason": str(exc)})
                continue
            if facts is None:
                report["companies"].append({"ticker": ticker, "status": "NO_SUPPLEMENT"})
                continue
            source = {
                "release_id": manifest["serving_release_id"],
                "artifact": entry.get("storage_key", base + path),
                "sha256": entry["sha256"],
                "sec_source": provenance,
                "candidate": True,
                "public_data_policy": "SEC fundamentals only; no warehouse market/provider prices",
            }
            try:
                packet = build_packet(ticker, cik, rows, facts, cutoff, source)
            except ProviderError as exc:
                report["companies"].append(
                    {"ticker": ticker, "status": "UNAVAILABLE", "reason": str(exc)})
                continue
            raw = json.dumps(packet, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode()
            sha = digest(raw)
            if len(raw) > 131072:
                raise ProviderError("Packet exceeds serving size limit.")
            key = f"gold/valuation/releases/{sha}/companies/{ticker}.json"
            if args.publish:
                transport.call("put", key, raw)
            packet_index[ticker] = {"key": key, "sha256": sha}
            item = {"ticker": ticker, "status": "READY",
                    "periods": [x["period_end"] for x in packet["historical"]],
                    "common_income_periods": len(packet.get("common_income", [])),
                    "has_adjustment_facts": "adjustment_facts" in packet,
                    "bytes": len(raw), "sha256": sha, "key": key}
            report["companies"].append(item)
            print(json.dumps(item), flush=True)

        if args.publish and packet_index:
            merged = {**prior_companies, **packet_index}
            pointer_doc = {
                "schema_version": "ppe-valuation-index-v1",
                "producer_release": manifest["serving_release_id"],
                "published_at": datetime.now(timezone.utc).isoformat(),
                "companies": merged,
            }
            pointer_raw = json.dumps(pointer_doc, sort_keys=True,
                                     separators=(",", ":")).encode()
            transport.call("put", args.pointer, pointer_raw,
                           expected_etag=transport.etags.get(args.pointer))
            report["candidate_pointer_sha256_after"] = digest(pointer_raw)
            report["candidate_companies_after"] = sorted(merged)
            report["published"] = True

        prod_after = transport.call("get", CandidateTransport.PRODUCTION_POINTER)
        raw_sha, canonical_sha = pointer_integrity(
            base64.b64decode(prod_after["body"]) if prod_after else None)
        report["production_pointer_sha256_after"] = raw_sha
        report["production_pointer_canonical_sha256_after"] = canonical_sha
        report["production_pointer_untouched"] = (
            report["production_pointer_sha256_before"] == report["production_pointer_sha256_after"])
        if args.publish and not report["production_pointer_untouched"]:
            raise ProviderError("Production pointer changed during candidate publication.")
        report["producer_release"] = manifest["serving_release_id"]
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    finally:
        archive.close()


if __name__ == "__main__":
    main()
