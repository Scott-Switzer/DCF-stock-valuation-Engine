CREATE TABLE IF NOT EXISTS provider_cache (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  expires REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS provider_cache_expiry ON provider_cache(expires);
