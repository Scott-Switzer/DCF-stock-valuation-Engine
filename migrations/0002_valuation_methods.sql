-- Preserve existing DCF rows while allowing methods without a present intrinsic value.
CREATE TABLE valuations_v2 (
 id TEXT PRIMARY KEY, created_at TEXT NOT NULL, model_version TEXT NOT NULL,
 ticker TEXT NOT NULL, valuation_date TEXT NOT NULL, source_kind TEXT NOT NULL,
 is_demo INTEGER NOT NULL CHECK (is_demo IN (0,1)),
 intrinsic_value REAL, target_price_12m REAL NOT NULL, market_price REAL NOT NULL,
 upside REAL, assumptions_json TEXT NOT NULL, financials_json TEXT NOT NULL,
 result_json TEXT NOT NULL, method TEXT NOT NULL DEFAULT 'dcf' CHECK(method IN ('dcf','ddm','relative')),
 client_hash TEXT NOT NULL, input_hash TEXT NOT NULL,
 UNIQUE(client_hash,input_hash)
);
INSERT INTO valuations_v2 SELECT id,created_at,model_version,ticker,valuation_date,source_kind,
 is_demo,intrinsic_value,target_price_12m,market_price,upside,assumptions_json,financials_json,
 result_json,'dcf',client_hash,input_hash FROM valuations;
DROP TABLE valuations;
ALTER TABLE valuations_v2 RENAME TO valuations;
CREATE INDEX valuations_ticker_date ON valuations(ticker,created_at);
CREATE INDEX valuations_method_date ON valuations(method,created_at);
