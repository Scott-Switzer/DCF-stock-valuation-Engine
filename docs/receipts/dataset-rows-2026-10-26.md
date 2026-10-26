# Catalogued dataset rows — release receipt

Date: 2026-10-26
Status: **merged and deployed; live acceptance passed on the shared query, MCP, CLI and website.**
Related: PR #92 (shared query), PR #94 (next-object paging), gateway PR #27 (MCP forwarding),
docs PR for this receipt.

## Why

The WRDS catalog registered **948 releases across 946 datasets** (~2.77 billion declared
rows; 864 with column schemas) and every consumer could only describe them. Responses
said licensed payloads were never returned, so the catalog was decorative. Nothing in
DCF, the CLI or MCP could read one row of CRSP, Compustat, IBES, TAQ, Capital IQ or the
other registered families.

## Shipped identities

| Component | Commit | Worker | Version | Previous |
| --- | --- | --- | --- | --- |
| Shared query | `8dd006d` (#92, #94) | `zion-security-funnel-staging` | `e2dd73ce-a47c-4410-8df3-9e9ebaea90b6` | `8e468054-9e6b-4efb-accd-8aad0e9e31c8` |
| MCP reader | `72735a1` (#27) | `zion-financial-mcp-staging` | `8824a564-ba43-40fc-9878-c1b5ce1328f8` | `8544bc4e-984c-4cd1-9b70-f1babce58662` |

Both deployed with `--keep-vars`. The funnel gained one service binding,
`ZION_DATASETS → zion-datasets`; no secret, bucket, object, queue or pointer changed.

## Contract

- `dataset_schema {dataset_id, object_index?}` — native parquet footer schema for one
  catalogue object of that dataset.
- `dataset_rows {dataset_id, object_index?, columns?, offset?, limit?, cursor?}` — one
  bounded page of native source rows. `limit` 1–1,000; `offset` ≤ 1e9; `columns` 1–64
  unique source names; `cursor` opaque and exclusive with `offset`.
- A caller names an **object index**, never a path: the catalog supplies the store and
  the key allowlist, so `path` is rejected as an unsupported field. The store must be
  `financial`, `research`, `filings` or `lakehouse`.
- Rows are returned under `result.records`, deliberately outside the bundle stamper's
  date scan, so `data_as_of` stays `null` rather than borrowing a row's date as
  coverage. Provenance carries `bundle_id`, `source_releases`, store, key, catalog
  `sha256`, `etag` and `catalog_release_id`.
- Every response reports `object_count` and `object_index`; when a page ends without a
  cursor, `next_object_index` names the object to read next (or `null` at the end). A
  cursor never crosses an object boundary, but a whole dataset is now walkable without
  guessing the catalogue order.
- Catalog or bundle drift fails closed before any object is read.

## Verified live (2026-10-26)

Dataset used: `crsp_a_stock__dse`, catalog id `105520548d1dc19878852367d31caa42`
(12,996,436 declared rows over 26 objects). Metadata only was recorded; no licensed
values were captured.

| Check | Result |
| --- | --- |
| `dataset_schema` (funnel, owner bearer) | 200; store `research`; key `raw/wrds/crsp_a_stock__dse/releases/20260920T035906Z/part-000000.parquet`; **50 columns**; footer declares **500,000** rows in 1 row group; `PARQUET_FOOTER_DECODED`; bundle `2c0419d1…`; `data_as_of: null` |
| `dataset_rows` (`columns`, limit 5) | 200; 5 records with exactly the requested keys; `row_count 500000`; `row_offset 0`; `next_cursor` present; `object_count 26`; `next_object_index null` while the cursor is live |
| After the paging deploy (#94) | `dataset_schema` reports `object_count 26`, `object_index 0`; the completion warning names the next object or the last of 26 |
| Cursor page | 200 at `row_offset 5`; default page size 100 rows when `limit` is omitted |
| `path: "raw/wrds/secret.parquet"` | 422 `INVALID_REQUEST: Unsupported field: path` |
| `limit: 5000` | 422 `Rows limit must be 1–1,000.` |
| Anonymous funnel request | 401 |
| MCP reader | tool scope still exactly `load_dcf_model`, `query_financial_data`; schema and rows return the same counts and bundle; `path` rejected at input validation |
| Website `/api/data/query` | 403 without a key ("Enter your private financial-system access key"), 200 with the owner bearer, 2 records |
| Installed CLI (`--request … --json`) | 200; same dataset, store and 50 columns |

## Not verified / limits

- No CRSP/Compustat/IBES field is yet mapped to a normalized financial fact. These rows
  are **source archives**: units, identity joins, availability and point-in-time
  semantics remain per-dataset work. Reading a row is not using it correctly.
- Licensed WRDS payloads stay private; no redistribution right is implied.
- `data_as_of` is `null` for row pages by design, so a caller must not read it as
  coverage or freshness.
- A cursor is still scoped to one object; crossing objects means a new request with
  `next_object_index` (now supplied) rather than one opaque cursor for the dataset.

## Rollback

```bash
# shared query
npx wrangler rollback 8e468054-9e6b-4efb-accd-8aad0e9e31c8 --config deploy/security-funnel/wrangler.jsonc
# MCP reader (from mcp/)
npx wrangler rollback 8544bc4e-984c-4cd1-9b70-f1babce58662
```

Reverting the MCP Worker alone removes the tool-level actions; the shared Worker keeps
the actions, which are owner-authenticated and unused by other callers.
