# Cloud valuation completion

Authorized scope: all 2,629 frozen symbols; reuse stored sources, run financial work
in private Cloudflare staging, preserve gaps, and review/merge the full-history PR.
PR #59 is merged at f5ec7e3. Production data promotion remains separate.

1. Audit existing canonical identities and accounting packets against current PPE gates.
2. Rebuild accounting packets from pinned SEC archive members already in R2 using
   the existing packet builder. Cache each full member once. Queue work in cloud;
   download only metadata. Verify hashes, archive identity, CRC, CIK and cutoff.
3. Persist independent accounting, identity, policy and assumption readiness. Never
   interpret a successful source read or packet build as a completed valuation.
4. Advance only eligible companies using company-specific historical drivers,
   current operating evidence and cited research. Require dated forecast paths,
   capital-cost inputs and terminal economics; no uniform growth/WACC defaults.
5. Run the existing model privately in cloud only after all required evidence is
   present; retain failed gates and source freshness. Reconcile all frozen symbols.
6. Review focused code checks and cloud receipts, publish the incremental PR, and
   merge only after checks and review pass. Do not promote production data pointers.

Current limitation: normalized nine-metric source inputs omit required accounting
concepts. The full SEC Company Facts members recover more fields, but explicit
common-shareholder income, preferred/minority claims and filing conflicts can
still block the existing model. A CIK or internal ticker key alone does not certify
a dated share-class/provider bridge. Neither gap is resolved with assumed zeros.
