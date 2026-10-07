"""Bounded TTL cache for public provider responses on Cloudflare D1."""

import json
import time


class EdgeStore:
    def __init__(self):
        from flask import request

        self.db = request.environ["workers.env"].DB

    def get(self, key):
        from pyodide.ffi import run_sync

        row = run_sync(
            self.db.prepare("SELECT value,expires FROM provider_cache WHERE key=?")
            .bind(key)
            .first()
        )
        if row and row.expires > time.time():
            return json.loads(str(row.value))
        return None

    def set(self, key, value, ttl):
        from pyodide.ffi import run_sync

        raw = json.dumps(value, allow_nan=False)
        if len(raw.encode()) > 1_500_000:
            return
        now = time.time()
        run_sync(
            self.db.prepare(
                "INSERT INTO provider_cache(key,value,expires) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,expires=excluded.expires"
            )
            .bind(key, raw, now + min(ttl, 21600))
            .run()
        )
        run_sync(self.db.prepare("DELETE FROM provider_cache WHERE expires<?").bind(now).run())
