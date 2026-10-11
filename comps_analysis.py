"""Explain peer distributions without silently filtering or winsorizing outliers."""

import statistics

BASIS_LABELS = {
    "latest_annual": "Latest reported annual financials (not TTM)",
    "forward_year_one": "Forward year-one estimates",
    "unspecified": "Denominator basis not recorded",
}


def peer_basis(peer):
    basis = peer.get("denominator_basis", "unspecified")
    if not isinstance(basis, str) or basis not in BASIS_LABELS:
        raise ValueError(f"Unsupported peer denominator basis for {peer.get('ticker')}.")
    return basis


def distribution(peers, key, forward, claims, shares, allowed=True):
    values = [p["multiples"][key] for p in peers
              if p.get("review_status") not in {"candidate", "excluded"}
              and p["multiples"].get(key) is not None and p["multiples"][key] > 0 and allowed]
    fences = None
    if len(values) >= 4:
        q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
        fences = (q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1))
    contributions = []
    for peer in peers:
        value = peer["multiples"].get(key)
        reason = None
        if peer.get("review_status") in {"candidate", "excluded"}:
            reason = "Peer not confirmed for inclusion"
        elif not allowed:
            reason = "Enterprise multiple is unsuitable for this target"
        elif value is None or value <= 0:
            reason = "Missing or nonpositive multiple"
        included = reason is None
        implied = ((value * forward - (claims if key.startswith("ev_") else 0)) / shares
                   if included and forward is not None and forward > 0 else None)
        contributions.append({
            "ticker": peer["ticker"], "name": peer.get("name"), "multiple": value,
            "included": included, "exclusion_reason": reason,
            "weight": 1 / len(values) if included else 0,
            "implied_price": max(0, implied) if implied is not None else None,
            "raw_implied_price": implied,
            "outlier": bool(included and fences and not fences[0] <= value <= fences[1]),
            "basis": peer_basis(peer), "period_end": peer.get("financial_period_end"),
            "price_as_of": peer.get("as_of"), "source": peer.get("source"),
            "review_status": peer.get("review_status", "manual"),
        })
    median = statistics.median(values) if values else None
    median_implied = ((median * forward - (claims if key.startswith("ev_") else 0)) / shares
                      if median is not None and forward is not None and forward > 0 else None)
    return {"median": median, "median_implied_price": max(0, median_implied) if median_implied is not None else None,
            "distribution": contributions,
            "outlier_rule": "1.5 × IQR using inclusive quartiles, at least four valid peers; flagged observations remain included",
            "outlier_count": sum(p["outlier"] for p in contributions)}
