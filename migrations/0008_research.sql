CREATE TABLE IF NOT EXISTS research_documents (
 id TEXT PRIMARY KEY, client_hash TEXT NOT NULL, created_at TEXT NOT NULL,
 parent_id TEXT, title TEXT NOT NULL, ticker TEXT NOT NULL, method TEXT NOT NULL,
 scenario_name TEXT NOT NULL, financial_hash TEXT NOT NULL,
 market_price REAL NOT NULL, target_price REAL NOT NULL, snapshot_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS research_owner_created ON research_documents(client_hash, created_at);
CREATE INDEX IF NOT EXISTS research_owner_financial ON research_documents(client_hash, financial_hash, created_at);
