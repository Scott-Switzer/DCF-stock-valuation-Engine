"""Read only the public, compact valuation namespace through an R2 binding."""

import hashlib
import json
import re
import time
from datetime import date, datetime, timezone
from dcf_loader import ProviderError, ticker_symbol
from ppe_packets import validate_packet

POINTER = "control/valuation/CURRENT.json"


def _wait(promise, deadline=None):
    """Bound every cache/R2 promise by the caller's shared monotonic deadline."""
    from pyodide.ffi import run_sync
    if deadline is None:
        return run_sync(promise)
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ProviderError("PPE read exceeded the shared request deadline.")
    import asyncio

    async def bounded():
        try:
            return await asyncio.wait_for(promise, timeout=remaining)
        except TimeoutError:
            raise ProviderError("PPE read exceeded the shared request deadline.") from None

    return run_sync(bounded())


def _object_json(bucket, key, *, maximum, digest=None, ttl=60, deadline=None):
    from pyodide.ffi import to_js
    from js import Object

    cache = cache_request = None
    raw = None
    from_cache = False
    try:
        from js import Request, Response, caches

        cache = caches.default
        cache_request = Request.new(
            "https://ppe-valuation.invalid/cache/" + hashlib.sha256(key.encode()).hexdigest()
        )
        cached = _wait(cache.match(cache_request), deadline)
        if cached:
            raw = str(_wait(cached.text(), deadline))
            from_cache = True
    except ProviderError:
        raise
    except Exception:
        pass
    if raw is None:
        try:
            obj = _wait(bucket.get(key), deadline)
        except ProviderError:
            raise
        except Exception:
            raise ProviderError("PPE storage is temporarily unavailable.") from None
        if not obj:
            return None
        try:
            if obj.size > maximum:
                raise ProviderError("PPE packet exceeds its serving budget.")
            raw = str(_wait(obj.text(), deadline))
        except ProviderError:
            raise
        except Exception:
            raise ProviderError("PPE storage body is temporarily unavailable.") from None
    if len(raw.encode()) > maximum:
        raise ProviderError("PPE packet exceeds its serving budget.")
    if digest and hashlib.sha256(raw.encode()).hexdigest() != digest:
        raise ProviderError("PPE packet integrity check failed.")
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        raise ProviderError("PPE packet is not valid JSON.") from None
    if not from_cache and cache is not None and cache_request is not None:
        try:
            response = Response.new(
                raw,
                to_js(
                    {"headers": {"Cache-Control": f"public, max-age={ttl}"}},
                    dict_converter=Object.fromEntries,
                ),
            )
            _wait(cache.put(cache_request, response), deadline)
        except Exception:
            # Cache availability never changes the authoritative read contract.
            pass
    return value


def load_packet(ticker, asof=None, *, deadline=None):
    from flask import current_app, request

    ticker = ticker_symbol(ticker)
    asof = asof or datetime.now(timezone.utc).date().isoformat()
    if date.fromisoformat(asof) > datetime.now(timezone.utc).date():
        raise ProviderError("Future PPE valuation dates are unavailable.")
    if not current_app.config.get("CLOUDFLARE"):
        return None
    bucket = getattr(request.environ["workers.env"], "PPE_DATA", None)
    if bucket is None:
        return None
    pointer = _object_json(bucket, POINTER, maximum=524288, deadline=deadline)
    if pointer is None:
        return None
    if (
        not isinstance(pointer, dict)
        or pointer.get("schema_version") != "ppe-valuation-index-v1"
        or not isinstance(pointer.get("companies"), dict)
    ):
        raise ProviderError("PPE valuation index schema mismatch.")
    entry = pointer.get("companies", {}).get(ticker)
    if not entry:
        return None
    if not isinstance(entry, dict):
        raise ProviderError("Invalid PPE packet reference.")
    key = entry.get("key", "")
    digest = entry.get("sha256", "")
    if (
        not isinstance(key, str)
        or not isinstance(digest, str)
        or not re.fullmatch(
            r"gold/valuation/releases/[a-f0-9]{64}/companies/" + re.escape(ticker) + r"\.json", key
        )
        or not re.fullmatch("[a-f0-9]{64}", digest)
    ):
        raise ProviderError("Invalid PPE packet reference.")
    packet = _object_json(bucket, key, maximum=131072, digest=digest, ttl=31536000, deadline=deadline)
    if packet is None:
        raise ProviderError("Published PPE packet is missing.")
    return validate_packet(packet, ticker, asof)


def prefer_ppe(document, ticker, asof, *, deadline=None):
    """Retain an explicit baseline when the public packet cannot be used."""
    from ppe_packets import apply_packet

    try:
        packet = load_packet(ticker, asof, deadline=deadline)
        if packet:
            candidate = apply_packet(document, packet, asof)
            from dcf_loader import parse_document

            try:
                parse_document(candidate)
            except ValueError:
                raise ProviderError(
                    "PPE fields do not meet the valuation model's input requirements."
                ) from None
            return candidate
        document["source"]["ppe_status"] = (
            "No published PPE valuation packet for this ticker; Yahoo fallback."
        )
    except ProviderError as exc:
        document["source"]["ppe_status"] = str(exc)
        document["source"].setdefault("warnings", []).append(
            "PPE packet unavailable or incompatible; using Yahoo financials with provenance."
        )
    return document
