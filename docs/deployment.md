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

Public calculation requests persist canonical financials, assumptions, model version and result to private D1 before returning success. Library cookies are Secure, HttpOnly and SameSite=Lax; on Workers they are signed with the request-bound LIBRARY_SECRET, or a separate key derived from the existing RECORD_SALT. The public development signing key is never used on Workers. Older network-scoped records remain private and are not automatically assigned to a browser. The method column and method-specific model version distinguish DCF, DDM and relative records; relative has no present intrinsic value. No public record-list or sentiment endpoint exists. HTML and API responses include a saved reference. CSV/JSON export requests do not insert records. Repeats with identical normalized inputs and the same browser library identity reuse the record. Different assumptions are retained; same-network users share the network rate limit. The network hash is derived using HMAC and a server secret for rate limiting; raw addresses are not stored in valuation rows. New valuation records belong to a persistent browser library identity, independently of network rate limiting. Cloudflare may retain platform security/log metadata.

Cloudflare native rate-limit bindings enforce preview, reference and write limits per network hash at each location. Writes are limited to ten per minute; this is not a global traffic quota. D1 stores valuation records and shared public-provider cache entries. It is basic abuse protection, not proof of distinct people or bot-free submissions. Records flag synthetic origins even if users relabel the example as manual. Saved results omit duplicate source/document copies and the serialized row is bounded below D1's row-size limit. Collection is described at `/privacy`. The owner can delete a record by its reference through authenticated D1 administration.

Accounts are optional email-and-password sign-ins. Passwords use PBKDF2-HMAC-SHA256 at 100,000 iterations, the maximum Workers WebCrypto accepts, and are stored only as salted hashes. Sessions are 256-bit random tokens in an HttpOnly, Secure, SameSite=Lax cookie; D1 stores only their SHA-256 digests and they expire after 14 days. Signing up or in moves the current browser library into the account. Changing the password revokes every other session. No verification or reset email is sent yet, so an account proves a password rather than mailbox control, and a forgotten password cannot be recovered. Migration `0005_accounts.sql` must be applied remotely before these routes are deployed.

The local CPython app does not collect valuation records. Its SQLite Store provides temporary process-safe cache/limits on a single host; those are separate from Cloudflare's D1 persistence.

## Providers

PPE compact public SEC packets overlay compatible financial fields on Yahoo ticker snapshots for DCF/DDM/RV and comparable companies. The `PPE_DATA` binding points to the existing financial-system-datasets bucket; serving reads only the separate valuation index and immutable company packets. Yahoo supplies current market inputs and labeled missing-field fallbacks. Migration 0003 adds a shared D1 cache for public provider responses; cache expiry is bounded to six hours. Provider calls have a shared request deadline. Unofficial endpoint failures remain visible.

SEC uses the configured contact identity and bounded Workers `fetch` calls. Successful live coverage does not eliminate filing review: missing facts and prices remain blank, eligibility needs confirmation, and dilution/debt classifications require review. Optional `ZION_API_BASE_URL`, `ZION_API_TOKEN`, `DCF_API_BASE_URL`, and `DCF_API_TOKEN` belong in Worker vars/secrets. The Zion-compatible custom company API adapter is implemented, but its endpoint and credentials are not configured in this release. No licensed upstream dataset is redistributed.

## Acceptance and rollback

Check `/health`, `/ready`, synthetic calculation, form validation, autocomplete, privacy disclosure and both exports on the public URL. Confirm the saved reference exists through an authenticated D1 query and repeat inputs do not add rows. Formula acceptance is covered by the independent CUIG reconciliation tests.

Before deploying the MCP and account changes, confirm that the rate-limit namespace IDs in `wrangler.jsonc` (including `MCP_LIMIT`, id `1946100604`) are not used by another binding in the Cloudflare account. Namespace IDs are self-chosen and need no creation step, and bindings that share an ID share counters. `/mcp` requires `MCP_LIMIT` on Workers. Add `/api/account/*` and `/account` to the post-deploy checks: signed-out 401, foreign-Origin 403, sign-up/sign-in/sign-out, and two-account library isolation.

Use `wrangler versions list` and `wrangler rollback` to restore a prior Worker version. D1 schema/data survive code rollback; apply only backward-compatible migrations unless planning a data migration. The old suspended Render service is left untouched and is no longer the advertised deployment. `render.yaml` and Docker remain optional local/self-hosting alternatives.

## Investment research migration

Before deploying the research workspace release, apply pending D1 migrations with `wrangler d1 migrations apply dcf-valuations --remote`, using the project's Python Wrangler wrapper. `0008_research.sql` only creates the research table and indexes; it preserves existing account and valuation records. Confirm no pending migrations remain. Preserve existing Worker variables with `--keep-vars`. Rollback to the prior Worker is compatible with the additive table.

Post-deploy: save a non-confidential test research revision, inspect its private report and JSON/XLSX exports, create a second revision and confirm the original is unchanged. A separate browser library must receive 404 for the report and exports. Confirm account sign-in still claims anonymous research and all existing library types. Notes are user-written; no source verification or email delivery is implied.
