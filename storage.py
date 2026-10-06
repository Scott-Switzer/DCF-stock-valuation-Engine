"""Process-safe local cache and rate limits. SQLite transactions are atomic."""

import json
import os
from pathlib import Path
import sqlite3
import time


class Store:
    def __init__(self, path=None):
        self.path = path or os.getenv("DCF_STATE_PATH", "/tmp/dcf-state.sqlite3")
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as c:
            c.execute(
                "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL, expires REAL NOT NULL)"
            )
            c.execute(
                "CREATE TABLE IF NOT EXISTS limits (key TEXT PRIMARY KEY, count INTEGER NOT NULL, reset REAL NOT NULL)"
            )

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def get(self, key):
        with self.connect() as c:
            row = c.execute("SELECT value,expires FROM cache WHERE key=?", (key,)).fetchone()
            if row and row[1] > time.time():
                return json.loads(row[0])
        return None

    def set(self, key, value, ttl):
        raw = json.dumps(value, allow_nan=False)
        with self.connect() as c:
            c.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)", (key, raw, time.time() + ttl))
            c.execute("DELETE FROM cache WHERE expires < ?", (time.time(),))

    def allow(self, key, maximum=10, window=60):
        now = time.time()
        with self.connect() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("DELETE FROM limits WHERE reset<=?", (now,))
            row = c.execute("SELECT count,reset FROM limits WHERE key=?", (key,)).fetchone()
            if row and row[0] >= maximum:
                return False
            c.execute(
                "INSERT OR REPLACE INTO limits VALUES (?,?,?)",
                (key, (row[0] + 1) if row else 1, row[1] if row else now + window),
            )
            return True
