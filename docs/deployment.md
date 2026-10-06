# Cloudflare deployment

The public application runs as a Python Cloudflare Worker at **https://dcf-valuation-engine.scswitzer.workers.dev**. It preserves the Flask views and pure Python model through Cloudflare's WSGI adapter. Private research records use a D1 binding, not the Worker's ephemeral filesystem.

## Reproduce deployment

Use Python 3.12+, Node.js and uv >=0.12.3. `uv sync` installs the pinned project dependencies and Python Workers CLI. The generated `pylock.toml` pins vendored runtime packages; `uv.lock` pins local tooling. Local pip installation using `requirements-dev.txt` remains supported.

```bash
uv sync
uv run pywrangler whoami
uv run pywrangler d1 migrations apply dcf-valuations --local
uv run pywrangler dev
uv run pywrangler deploy --dry-run
uv run pywrangler d1 migrations apply dcf-valuations --remote
uv run pywrangler deploy
```

For another account, create its own D1 database and update the account/database IDs in `wrangler.jsonc`. Set `RECORD_SALT` with `wrangler secret put RECORD_SALT` before receiving public traffic. It must be a randomly generated secret; never commit it. For local Workers development, put a separate random value in ignored `.dev.vars`. The build embeds public templates, CSS, JavaScript and sample data into an isolated generated `worker_runtime/` bundle; no environments, local secrets, tests or personal workbook are uploaded.

## Data and abuse controls

Public calculation requests persist canonical financials, assumptions, model version and result to private D1 before returning success. No public record-list or sentiment endpoint exists. HTML and API responses include a saved reference. CSV/JSON export requests do not insert records. Repeats with identical normalized inputs and the same daily network hash reuse the record. Different assumptions are retained; same-network users can share the deduplication and rate limit. The hash is derived using HMAC and a server secret; raw addresses are not stored in valuation rows. Cloudflare may retain platform security/log metadata.

D1 enforces an atomic shared limit of ten POST requests per network hash per calendar minute. This covers the deployed Worker across isolates. It is basic abuse protection, not proof of distinct people or bot-free submissions. Records flag synthetic origins even if users relabel the example as manual. Saved results omit duplicate source/document copies and the serialized row is bounded below D1's row-size limit. Collection is disclosed before calculation and at `/privacy`. The owner can delete a record by its reference through authenticated D1 administration.

The local CPython app does not collect valuation records. Its SQLite Store provides temporary process-safe cache/limits on a single host; those are separate from Cloudflare's D1 persistence.

## Providers

SEC uses the configured contact identity and bounded Workers `fetch` calls. Successful live coverage does not eliminate filing review: missing facts and prices remain blank, eligibility needs confirmation, and dilution/debt classifications require review. Optional `ZION_API_BASE_URL`, `ZION_API_TOKEN`, `DCF_API_BASE_URL`, and `DCF_API_TOKEN` belong in Worker vars/secrets. Zion is an implemented adapter, but its endpoint and credentials are not configured in this release. No licensed upstream dataset is redistributed.

## Acceptance and rollback

Check `/health`, `/ready`, synthetic calculation, form validation, autocomplete, privacy disclosure and both exports on the public URL. Confirm the saved reference exists through an authenticated D1 query and repeat inputs do not add rows. Formula acceptance is covered by the independent CUIG reconciliation tests.

Use `wrangler versions list` and `wrangler rollback` to restore a prior Worker version. D1 schema/data survive code rollback; apply only backward-compatible migrations unless planning a data migration. The old suspended Render service is left untouched and is no longer the advertised deployment. `render.yaml` and Docker remain optional local/self-hosting alternatives.
