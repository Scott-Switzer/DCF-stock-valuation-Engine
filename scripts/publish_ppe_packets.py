"""Bounded public SEC packet publication; existing producer pointers are read-only.

Run with --symbols AAPL first. --all reads published annual fundamentals one issuer
at a time, never market-price objects. SEC supplements are explicit local public
companyfacts inputs; this command never calls a provider or triggers acquisition.
"""

import argparse
import base64
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ppe_packets import build_packet
from dcf_loader import ProviderError, ticker_symbol


class R2:
    def __init__(self, config):
        self.etags = {}
        self.process = subprocess.Popen(
            ["node", str(Path(__file__).with_name("ppe_r2_bridge.mjs")), config],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=os.environ,
        )

    def call(self, op, key="", raw=None, expected_etag=None, items=None):
        cmd = {"op": op, "key": key, "expectedEtag": expected_etag}
        if items is not None:
            cmd["items"] = items
        if raw is not None:
            cmd["body"] = base64.b64encode(raw).decode()
        self.process.stdin.write(json.dumps(cmd) + "\n")
        self.process.stdin.flush()
        for line in self.process.stdout:
            if not line.startswith("R2JSON"):
                continue
            result = json.loads(line[6:])
            if result.get("error"):
                raise ProviderError("Remote R2 operation failed for " + key)
            return result.get("result")
        raise ProviderError("Remote R2 proxy stopped.")

    def get(self, key, digest=None):
        result = self.call("get", key)
        if result is None:
            return None
        self.etags[key] = result.get("etag")
        raw = base64.b64decode(result["body"])
        if digest and hashlib.sha256(raw).hexdigest() != digest:
            raise ProviderError("Immutable artifact hash mismatch.")
        return json.loads(raw)

    def close(self):
        self.process.stdin.write('{"op":"close"}\n')
        self.process.stdin.flush()
        self.process.stdin.close()
        self.process.wait(timeout=15)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--symbols", default="AAPL")
    parser.add_argument("--all", action="store_true")
    parser.add_argument(
        "--sec-facts", action="append", default=[], help="TICKER=/path/public-companyfacts.json"
    )
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    sec = {}
    for pair in args.sec_facts:
        ticker, path = pair.split("=", 1)
        raw = Path(path).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        sec[ticker_symbol(ticker)] = (json.loads(raw), raw, digest)
    r2 = R2(args.config)
    cutoff = datetime.now(timezone.utc).date().isoformat()
    report = {"cutoff_date": cutoff, "companies": [], "published": False}
    try:
        pointer = r2.get("gold/serving/coverage25/CURRENT.json")
        manifest = r2.get(pointer["manifest_key"], pointer["manifest_sha256"])
        base = "gold/serving/releases/" + manifest["serving_release_id"] + "/"
        entries = {x["path"]: x for x in manifest["artifacts"]}

        def artifact(path):
            entry = entries[path]
            return r2.get(entry.get("storage_key", base + path), entry["sha256"])

        index = artifact("identity/resolver_index.json")
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        # Discover resolver shape from the producer contract, never guess symbol paths.
        from typing import Any

        def symbol_entries(value: Any):
            if isinstance(value, dict):
                if value.get("symbol") and value.get("artifact_path"):
                    yield value
                for v in value.values():
                    yield from symbol_entries(v)
            elif isinstance(value, list):
                for v in value:
                    yield from symbol_entries(v)

        resolved = {}
        for entry in symbol_entries(index):
            try:
                symbol = ticker_symbol(entry["symbol"])
            except ValueError:
                if args.all:
                    report["companies"].append(
                        {"ticker": entry["symbol"], "status": "UNSUPPORTED_SYMBOL"}
                    )
                continue
            resolved.setdefault(symbol, entry)
        wanted = (
            sorted(resolved) if args.all else [ticker_symbol(x) for x in args.symbols.split(",")]
        )
        packet_index = {}
        prefetched = {}
        pending_writes = []
        for position, ticker in enumerate(wanted):
            if position % 4 == 0:
                if pending_writes:
                    r2.call("batch", items=pending_writes)
                    pending_writes = []
                group = wanted[position : position + 4]
                requests = []
                paths = []
                for symbol in group:
                    path = resolved[symbol]["artifact_path"] + "/fundamentals/annual.json"
                    if path in entries:
                        paths.append(path)
                        requests.append(
                            {"op": "get", "key": entries[path].get("storage_key", base + path)}
                        )
                results = r2.call("batch", items=requests)
                prefetched = {}
                for path, result in zip(paths, results):
                    if result is None:
                        raise ProviderError("Published annual artifact missing.")
                    raw = base64.b64decode(result["body"])
                    if hashlib.sha256(raw).hexdigest() != entries[path]["sha256"]:
                        raise ProviderError("Immutable artifact hash mismatch.")
                    prefetched[path] = json.loads(raw)

            if ticker not in resolved:
                raise ProviderError("Ticker absent from published identity resolver: " + ticker)
            entity = resolved[ticker]
            path = entity["artifact_path"] + "/fundamentals/annual.json"
            entry = entries.get(path)
            if not entry:
                report["companies"].append({"ticker": ticker, "status": "NO_ANNUAL_ARTIFACT"})
                continue
            rows = prefetched[path]
            rows = rows if isinstance(rows, list) else rows.get("rows", [])
            issuer = re.search(r"entity_sec_cik_([0-9]{10})(?:_[A-Z-]+)?$", entity["artifact_path"])
            if not issuer:
                raise ProviderError("Unsupported SEC issuer path.")
            cik = issuer.group(1)
            source = {
                "release_id": manifest["serving_release_id"],
                "artifact": entry.get("storage_key", base + path),
                "sha256": entry["sha256"],
                "public_data_policy": "SEC fundamentals only; no warehouse market/provider prices",
            }
            facts = None
            if ticker in sec:
                facts, raw, digest = sec[ticker]
                source["sec_source"] = {
                    "artifact": "raw/valuation-sec/" + digest + "/companyfacts.json",
                    "sha256": digest,
                    "url": "https://data.sec.gov/api/xbrl/companyfacts/CIK" + cik + ".json",
                }
                if args.publish:
                    r2.call("put", source["sec_source"]["artifact"], raw)
            try:
                packet = build_packet(ticker, cik, rows, facts, cutoff, source)
            except ProviderError as exc:
                if not args.all:
                    raise
                report["companies"].append(
                    {"ticker": ticker, "status": "UNAVAILABLE", "reason": str(exc)}
                )
                continue
            raw = json.dumps(
                packet, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
            digest = hashlib.sha256(raw).hexdigest()
            key = "gold/valuation/releases/" + digest + "/companies/" + ticker + ".json"
            if len(raw) > 131072:
                raise ProviderError("Packet exceeds serving size limit.")
            if args.publish:
                pending_writes.append(
                    {"op": "put", "key": key, "body": base64.b64encode(raw).decode()}
                )
            packet_index[ticker] = {"key": key, "sha256": digest}
            item = {
                "ticker": ticker,
                "status": "READY",
                "periods": [x["period_end"] for x in packet["historical"]],
                "fields": sum(
                    v is not None for row in packet["historical"] for v in row["fields"].values()
                ),
                "dividend_periods": len(packet["dividends"]),
                "bytes": len(raw),
            }
            report["companies"].append(item)
            print(json.dumps(item), flush=True)
            Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
        if args.publish:
            if pending_writes:
                r2.call("batch", items=pending_writes)
            prior = r2.get("control/valuation/CURRENT.json") or {"companies": {}}
            # Incremental publications retain previously published issuer packets.
            index = {
                "schema_version": "ppe-valuation-index-v1",
                "producer_release": manifest["serving_release_id"],
                "published_at": datetime.now(timezone.utc).isoformat(),
                "companies": {**prior.get("companies", {}), **packet_index},
            }
            r2.call(
                "put",
                "control/valuation/CURRENT.json",
                json.dumps(index, sort_keys=True, separators=(",", ":")).encode(),
                expected_etag=r2.etags.get("control/valuation/CURRENT.json"),
            )
            report["published"] = True
        report["producer_release"] = manifest["serving_release_id"]
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    finally:
        r2.close()


if __name__ == "__main__":
    main()
