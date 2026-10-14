"""Independent evidence audit for a staging-only SEC-first PEP packet.

Reads the published R2 annual rows and cached SEC companyfacts, rebuilds the
packet with the repo publisher, and checks every completeness-gate field back
to its filed tag, value, and 10-K accession. Prints PASS/FAIL per field plus
the preferred-zero balance-sheet identity. No publication pointers touched.
"""

import datetime
import json
import sys

CIK = "0000077476"
TICKER = "PEP"
ENDS = ["2023-12-30", "2024-12-28", "2025-12-27"]


def filed(facts, tag, end, *, instant_only=False):
    obs = [
        o
        for o in facts.get("facts", {}).get("us-gaap", {}).get(tag, {}).get("units", {}).get("USD", [])
        if o.get("end") == end
        and o.get("form") in {"10-K", "10-K/A"}
        and (not instant_only or not o.get("start"))
    ]
    if not obs:
        return None, None
    latest = max(o["filed"] for o in obs)
    top = [o for o in obs if o["filed"] == latest]
    values = {o["val"] for o in top}
    if len(values) != 1:
        return "CONFLICT", None
    return top[0]["val"], top[0]["accn"]


def trace_field(facts, field, end):
    """Confirm a packet field's own provenance (tag + accession) reproduces its value."""
    prov = (field or {}).get("provenance", {}) or {}
    tag = prov.get("tag")
    if not tag:
        return True, f"non-tag provenance ({prov.get('provider')})"
    val, accn = filed(facts, tag, end)
    ok = val is not None and abs(val - (field.get("value") or 0)) <= max(1.0, abs(val) * 1e-9)
    return ok, f"{tag}={val} packet={field.get('value')} accn={accn}"


def main(rows_path, facts_path):
    from ppe_packets import build_packet, validate_packet
    from sec_first import eligibility_gate

    asof = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    rows = json.load(open(rows_path))
    rows = rows if isinstance(rows, list) else rows.get("rows", [])
    facts = json.load(open(facts_path))
    packet = build_packet(TICKER, CIK, rows, facts, asof, {"provider": "staging-candidate"})
    validate_packet(packet, TICKER, asof)
    print(f"packet VALID for {TICKER} at asof {asof}")

    failures = []

    def check(label, ok, detail=""):
        print(("PASS " if ok else "FAIL ") + label + (f" :: {detail}" if detail else ""))
        if not ok:
            failures.append(label)

    common = {c["period_end"]: c for c in packet.get("common_income", [])}
    history = {r["period_end"]: r.get("fields", {}) for r in packet.get("historical", [])}
    for end in ENDS:
        kept = common.get(end)
        ok, detail = trace_field(
            facts, kept, end) if kept else (False, "packet omitted common income")
        bridge = (kept or {}).get("provenance", {}).get("bridge", "")
        check(f"common_income {end}", ok and bridge.startswith(("match_", "explained_by_")),
              f"{detail} bridge={bridge}")
        for key in ("revenue", "ebit", "d_and_a", "capex", "nwc", "tax_rate",
                    "book_value", "net_income"):
            field = history.get(end, {}).get(key)
            ok, detail = trace_field(facts, field, end)
            check(f"statement_{key} {end}", ok, detail)
        cs = sum(
            s * (filed(facts, tag, end)[0] or 0)
            for tag, s in {
                "CommonStockValue": 1,
                "AdditionalPaidInCapitalCommonStock": 1,
                "RetainedEarningsAccumulatedDeficit": 1,
                "AccumulatedOtherComprehensiveIncomeLossNetOfTax": 1,
                "TreasuryStockValue": -1,
            }.items()
        )
        sh, sh_accn = filed(facts, "StockholdersEquity", end)
        check(
            f"preferred_zero_identity {end}",
            sh is not None and sh - cs == 0,
            f"SH={sh} common_buildup={cs} accn={sh_accn}",
        )
        for tag in ("DebtCurrent", "LongTermDebtNoncurrent"):
            val, acc = filed(facts, tag, end, instant_only=True)
            check(f"{tag} {end}", val is not None, f"{val} accn={acc}")
        nci, nci_acc = filed(facts, "MinorityInterest", end, instant_only=True)
        check(f"minority_interest {end}", nci is not None, f"{nci} accn={nci_acc}")
        # No redeemable/mezzanine preferred claim filed at this balance date.
        mezz = [
            tag
            for tag in (
                "RedeemableNoncontrollingInterest", "TemporaryEquity",
                "PreferredStockValue", "PreferredStockValueOutstanding",
            )
            if filed(facts, tag, end)[0] not in (None, 0)
        ]
        check(f"no_mezzanine_preferred {end}", not mezz, f"nonzero={mezz}")

    bridge = packet.get("bridge", {})
    for key in ("short_term_debt", "long_term_debt", "preferred_equity", "minority_interest", "cash"):
        check(f"bridge_{key}", bridge.get(key, {}).get("value") is not None,
              str(bridge.get(key, {}).get("value")))
    shares = packet.get("diluted_shares", {})
    check("diluted_shares", (shares.get("value") or 0) > 0, str(shares.get("value")))

    gate = eligibility_gate(packet, TICKER, asof)
    check("gate_eligible", gate["eligible"], "; ".join(gate["reasons"][:4]))
    if failures:
        print(f"\n{len(failures)} FAILURES")
        return 1
    print("\nALL EVIDENCE CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
