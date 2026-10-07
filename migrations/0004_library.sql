CREATE TABLE IF NOT EXISTS templates (
 id TEXT PRIMARY KEY, created_at TEXT NOT NULL, client_hash TEXT NOT NULL,
 name TEXT NOT NULL, method TEXT NOT NULL, assumptions_json TEXT NOT NULL,
 UNIQUE(client_hash, name)
);
CREATE TABLE IF NOT EXISTS share_links (
 token TEXT PRIMARY KEY, valuation_id TEXT NOT NULL, created_at TEXT NOT NULL,
 client_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS watchlist (
 client_hash TEXT NOT NULL, ticker TEXT NOT NULL, target REAL NOT NULL,
 direction TEXT NOT NULL CHECK(direction IN ('above','below')),
 created_at TEXT NOT NULL, PRIMARY KEY (client_hash, ticker)
);
