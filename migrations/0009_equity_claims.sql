CREATE TABLE IF NOT EXISTS equity_claims_bridges (
 id TEXT PRIMARY KEY, client_hash TEXT NOT NULL, created_at TEXT NOT NULL,
 ticker TEXT NOT NULL, cik TEXT NOT NULL, valuation_date TEXT NOT NULL,
 release_id TEXT, member_sha256 TEXT, scenario_name TEXT NOT NULL,
 enterprise_value REAL NOT NULL, equity_value REAL, value_per_share REAL,
 receipt_json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS equity_claims_owner_created ON equity_claims_bridges(client_hash, created_at);
CREATE INDEX IF NOT EXISTS equity_claims_owner_ticker ON equity_claims_bridges(client_hash, ticker, created_at);
