CREATE TABLE IF NOT EXISTS valuations (
 id TEXT PRIMARY KEY, created_at TEXT NOT NULL, model_version TEXT NOT NULL,
 ticker TEXT NOT NULL, valuation_date TEXT NOT NULL, source_kind TEXT NOT NULL,
 is_demo INTEGER NOT NULL CHECK (is_demo IN (0,1)),
 intrinsic_value REAL NOT NULL, target_price_12m REAL NOT NULL, market_price REAL NOT NULL,
 upside REAL NOT NULL, assumptions_json TEXT NOT NULL, financials_json TEXT NOT NULL,
 result_json TEXT NOT NULL, client_hash TEXT NOT NULL, input_hash TEXT NOT NULL,
 UNIQUE(client_hash, input_hash)
);
CREATE INDEX IF NOT EXISTS valuations_ticker_date ON valuations(ticker, created_at);
CREATE TABLE IF NOT EXISTS request_limits (key TEXT PRIMARY KEY, count INTEGER NOT NULL, reset INTEGER NOT NULL);
