# Financial information cutoff implementation plan

> Execute inline with superpowers:executing-plans; use one fresh review at the end. User has authorized autonomous implementation, merge, publication and deployment.

- [x] Add failing tests for strict timestamps, cutoff forwarding, annual packet bypass, echoed-cutoff mismatch and later/missing source availability.
- [x] Add a focused shared cutoff validator and wire it into query-input, annual reads and native period reads. Preserve bounded reads and explicit metadata.
- [x] Add MCP schema acceptance/rejection and forwarding tests; expose the same field.
- [ ] Run focused suites, review the branches, merge and deploy existing shared query/MCP Workers with existing bindings.
- [ ] Verify historical before/after filing behavior through source-pinned live requests; retain sanitized evidence and state remaining portfolio-readiness limits.
