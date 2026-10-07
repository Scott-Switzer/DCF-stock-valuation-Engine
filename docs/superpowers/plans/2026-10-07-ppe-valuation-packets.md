# PPE valuation packets implementation plan

Goal: ticker autofill prefers verified PPE financials, supplements missing fields from existing SEC evidence, and clearly labels Yahoo fallbacks.

Architecture: publish bounded compact immutable per-company packets to the existing financial-system-datasets R2 bucket. A separate valuation pointer references these packets; existing producer CURRENT pointers and acquisition jobs remain untouched. The valuation Worker reads packets through an R2 binding, exposes a bounded company API, and overlays only compatible dated fields on its Yahoo market/cost baseline.

Tasks:
- [x] Inspect published manifest source and existing SEC raw coverage; identify annual duration/instant/dilution mappings.
- [x] Write failing tests for period, unit, revision, missing-data, provenance, integrity and overlay behavior.
- [x] Implement pure packet builder and bounded read/publish CLI; verify AAPL, then expand available published universe without new acquisition.
- [x] Implement R2 packet reader, company API, automatic loading overlay and field-level coverage UI.
- [ ] Test DCF/DDM/RV, review, CI, publish packets and deploy; verify live and merge when checks/review pass.

Constraints: no licensed market/provider payloads on local disk or in public packets; SEC fundamentals only. Use authoritative immutable manifests and hashes. Availability is publication/filing time, not retrieved_at. Missing facts remain missing. Preserve dirty PPE/Zion primary checkouts. No upstream pointer updates or processing triggers. Yahoo current market data remains a clearly dated fallback; cached coverage never claims real time. Any future-as-of packet reads reject unavailable observations. Financial-firm eligibility remains enforced.

Review focus: annual vs quarterly duration; share basis vs instant outstanding; conflicting revisions; split debt/double counting; missing absence vs zero; stale facts/market observations; packet integrity, size and symbol matching; unknown ticker fallback; exact-head CI and live binding execution.
