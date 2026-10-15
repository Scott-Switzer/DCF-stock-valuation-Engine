"""The DCF application's integrated consumer of the Zion equity claims service.

`equity_claims_provider` verifies the versioned claims contract and maps it onto the
existing enterprise-to-equity bridge; this module is what makes that flow a real
deployment behavior inside the DCF Worker: the transport, the API route and the saved
research record.

Transport discipline
--------------------
The DCF Worker does not call Zion over the public internet. It calls the Cloudflare
service binding named by ``ZION_FINANCIAL_QUERY``, so the request resolves inside the
owner's account: no public hostname, no DNS, no external egress, and no bearer
credential placed on a wire. Authorization is nevertheless explicit -- the binding
carries a scoped service credential and an approved caller name, and the Zion route
accepts that credential only on ``/private/v1/equity-claims``.

Trust discipline
----------------
A matching SHA-256 proves that the bytes are internally consistent, not that Zion
produced them. Authenticity here rests on three separate things, all retained in
every saved record:

* the release pin (``release_id``, registry and manifest digests) that names the exact
  immutable archive the claims came from;
* the scoped service credential, compared in constant time by the answering service,
  which is what makes an answer attributable to Zion at all;
* the HMAC evidence attestation on the native history bundle, which is what makes the
  enterprise value this bridge consumes server-attested rather than caller-supplied.

The caller never supplies the enterprise value. This route recomputes it from the
attested bundle with the existing ``enterprise_valuation.value_enterprise`` engine, so
a client that wants a different enterprise value has to change an assumption, not a
number in the request.
"""

import hashlib
import json
import re
import uuid

import library
from dcf_loader import ProviderError, iso_date, provider_setting, ticker_symbol
from equity_claims_provider import (
    ADAPTER_VERSION,
    CLAIMS_PATH,
    SERVICE_CALLER,
    load_equity_claims,
    term_consistency,
    value_per_share,
)
from equity_claims_provider import ProviderError as ClaimsError

BINDING_NAME = 'ZION_FINANCIAL_QUERY'
SERVICE_TOKEN_SETTING = 'ZION_SERVICE_TOKEN'
CALLER_SETTING = 'ZION_EQUITY_CLAIMS_CALLER'
# A service binding ignores the request host: the binding itself selects the Worker.
# An absolute URL is still required because the claims contract builds ordinary URLs.
BINDING_ORIGIN = 'https://zion.internal'
TIMEOUT_MS = 20000
MAX_RECORD_BYTES = 1_500_000
SUMMARY_COLUMNS = ('id,created_at,ticker,cik,valuation_date,release_id,scenario_name,'
                   'enterprise_value,equity_value,value_per_share')


def fail(message):
    raise ProviderError('Zion equity claims service: ' + message)


def sync(awaitable):
    """The Worker runtime's bridge from async bindings to the sync WSGI app.

    Indirected so the transport can be driven by an ordinary test double too.
    """
    from pyodide.ffi import run_sync

    return run_sync(awaitable)


def request_target(url, headers, params):
    """Absolute URL and string headers for one claims request."""
    from urllib.parse import urlencode

    query = urlencode({key: value for key, value in (params or {}).items() if value is not None})
    return (f'{url}?{query}' if query else url,
            {str(key): str(value) for key, value in (headers or {}).items()})


def service_binding():
    """The bound Zion service object, or None when this runtime is not bound."""
    try:
        from flask import current_app, has_request_context, request

        if current_app.config.get('CLOUDFLARE') and has_request_context():
            return getattr(request.environ.get('workers.env'), BINDING_NAME, None)
    except (ImportError, RuntimeError, KeyError):
        return None
    return None


def configured_caller():
    """The internal caller name this deployment identifies itself with."""
    return provider_setting(CALLER_SETTING) or SERVICE_CALLER


class ServiceBindingHTTP:
    """A requests-compatible ``get`` that never leaves the account.

    The claims provider owns the credential headers and the response verification; this
    class owns only the transport, so an ordinary HTTPS session, a binding and a test
    double all run the exact same provider checks.
    """

    def __init__(self, binding, *, timeout_ms=TIMEOUT_MS):
        self.binding = binding
        self.timeout_ms = timeout_ms

    def get(self, url, headers=None, params=None):
        if self.binding is None:
            fail('no internal service binding is configured on this deployment')
        return sync(self._request(url, headers, params))

    async def dispatch(self, target, headers):
        """Send one request through the binding; the only runtime-specific step.

        `Request.new` takes a JavaScript init object. A plain Python dict reaches it as a
        Map, which the constructor rejects with a fatal isolate error rather than a typed
        failure, so the init is converted with `to_js(..., Object.fromEntries)` for the
        object shape the constructor requires.
        """
        from js import Object, Request
        from pyodide.ffi import to_js

        init = to_js({'headers': dict(headers)}, dict_converter=Object.fromEntries)
        return await self.binding.fetch(Request.new(target, init))

    async def _request(self, url, headers, params):
        import asyncio

        target, prepared = request_target(url, headers, params)
        try:
            response = await asyncio.wait_for(self.dispatch(target, prepared),
                                             self.timeout_ms / 1000)
        except TimeoutError:
            # The consumer stops waiting; a subrequest already in flight is not recalled.
            fail(f'the internal service did not answer within {self.timeout_ms} ms')
        body = await response.text()
        try:
            payload = json.loads(body)
        except ValueError:
            fail('the internal service returned a body that is not JSON')
        if not isinstance(payload, dict):
            fail('the internal service did not return a JSON object')
        try:
            # NaN and Infinity are not representable in the contract either.
            json.dumps(payload, allow_nan=False)
        except ValueError:
            fail('the internal service returned a nonfinite number')
        if response.status != 200:
            error = payload.get('error')
            code = error.get('code') if isinstance(error, dict) else None
            fail(f'the internal service refused the request with HTTP {response.status}'
                 + (f' ({code})' if code else ''))
        return payload


def load_claims(ticker, asof, *, cik, http=None, expected_release_id=None, source_asof=None,
                expected_source_release_id=None):
    """Fetch, verify and normalise Zion claims for one filer over the binding."""
    transport = http if http is not None else ServiceBindingHTTP(service_binding())
    caller = configured_caller()
    if caller != SERVICE_CALLER:
        fail('the configured internal caller is not an approved caller')
    try:
        return load_equity_claims(
            ticker_symbol(ticker), asof, transport, cik=cik, base=BINDING_ORIGIN,
            service_token=provider_setting(SERVICE_TOKEN_SETTING), caller=caller,
            expected_release_id=expected_release_id, source_asof=source_asof,
            expected_source_release_id=expected_source_release_id)
    except ClaimsError as exc:
        raise ProviderError(str(exc)) from exc


def bridge_scenario(ticker, asof, *, cik, enterprise_value, http=None, expected_release_id=None,
                    preferred_terms=None, scenario='AS_CONVERTED_MAX_RATE',
                    noncontrolling_policy='DEDUCT_REPORTED', source_asof=None,
                    expected_source_release_id=None):
    """One per-share common equity scenario from verified claims and an enterprise value.

    The enterprise value arrives from the server-side DCF engine, never from the client.
    `source_asof` pins the SEC evidence cutoff, which may be older than the valuation date
    when the valuation runs past the newest immutable SEC snapshot.
    """
    if isinstance(enterprise_value, bool) or not isinstance(enterprise_value, (int, float)):
        raise ValueError('A finite positive enterprise value is required.')
    number = float(enterprise_value)
    if not number > 0 or number in (float('inf'), float('-inf')) or number != number:
        raise ValueError('A finite positive enterprise value is required.')
    claims = load_claims(ticker, asof, cik=cik, http=http,
                         expected_release_id=expected_release_id, source_asof=source_asof,
                         expected_source_release_id=expected_source_release_id)
    result = value_per_share(number, claims, preferred_terms=preferred_terms,
                             scenario=scenario, noncontrolling_policy=noncontrolling_policy)
    if not isinstance(result.get('source', {}).get('release_id'), str):
        fail('a verified claims response without a release pin cannot be recorded')
    return dict(result, cik=cik, enterprise_scenario_value=number,
                term_consistency=(term_consistency(claims, preferred_terms)
                                  if preferred_terms is not None else {'status': 'NOT_APPLICABLE'}),
                attestation=dict(
                    transport='CLOUDFLARE_SERVICE_BINDING',
                    binding=BINDING_NAME,
                    adapter_version=ADAPTER_VERSION,
                    release_id=result['source']['release_id'],
                    member_sha256=result['source'].get('member_sha256'),
                    registry_sha256=result['source'].get('registry_sha256'),
                    manifest_sha256=result['source'].get('manifest_sha256'),
                    # Claims come from a companion Company Facts release, and the engine
                    # release separately pins the digest of the raw archive member. Both
                    # are recorded, and the consumer has already required them to agree.
                    source_release_id=result['source'].get('source_bundle', {}).get('source_release_id'),
                    source_manifest_sha256=result['source'].get('source_bundle', {}).get(
                        'source_manifest_sha256'),
                    source_reconciliation=result['source'].get('source_bundle', {}).get(
                        'reconciliation_status'),
                    bulk_archive_etag=result['source'].get('source_bundle', {}).get(
                        'bulk_archive_etag'),
                    evidence_ceiling_utc=result['source'].get('source_bundle', {}).get(
                        'evidence_ceiling_utc'),
                    evidence_cutoff=result['source'].get('evidence_cutoff'),
                    bridge_valuation_date=result['source'].get('bridge_valuation_date'),
                    claim_evidence_digests='RECOMPUTED_BY_CONSUMER',
                    digest_proves_authenticity=False,
                    interpretation=(
                        'Claim digests detect tampering with a received payload. '
                        'Authenticity comes from the scoped service credential and the dual '
                        'release pins, which name the answering service and the immutable '
                        'archives.'),
                ))


def save_bridge(record):
    primary = record.get('primary') or {}
    source = record.get('source') or {}
    # A record that cannot name the immutable archive it came from cannot be attributed
    # later, so it is refused rather than stored with an empty provenance.
    if not isinstance(source.get('release_id'), str):
        fail('a bridge without a release pin cannot be saved')
    encoded = json.dumps(record, allow_nan=False, sort_keys=True)
    if len(encoded.encode()) > MAX_RECORD_BYTES:
        raise ValueError('The bridge receipt is too large to save.')
    identity, created = str(uuid.uuid4()), library.now()
    library._run(
        'INSERT INTO equity_claims_bridges (id,client_hash,created_at,ticker,cik,valuation_date,'
        'release_id,member_sha256,scenario_name,enterprise_value,equity_value,value_per_share,'
        'receipt_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (identity, library.caller_hash(), created, record['ticker'], record['cik'],
         record['valuation_date'], source.get('release_id'), source.get('member_sha256'),
         record['primary_scenario'], record['enterprise_scenario_value'],
         primary.get('equity_value'), primary.get('value_per_share'), encoded))
    return get_bridge(identity)


def get_bridge(identity):
    rows = library._fetchall(
        f'SELECT {SUMMARY_COLUMNS},receipt_json FROM equity_claims_bridges WHERE id=? AND client_hash=?',
        (identity, library.caller_hash()))
    if not rows:
        return None
    row = rows[0]
    row['receipt'] = json.loads(row.pop('receipt_json'))
    return row


def list_bridges(ticker=None):
    sql = f'SELECT {SUMMARY_COLUMNS} FROM equity_claims_bridges WHERE client_hash=?'
    params = [library.caller_hash()]
    if ticker:
        sql += ' AND ticker=?'
        params.append(ticker_symbol(ticker))
    sql += ' ORDER BY created_at DESC,id DESC LIMIT 50'
    return library._fetchall(sql, tuple(params))


def bridge_fingerprint(record):
    """Stable identity of a saved bridge, for receipts written outside the database."""
    canonical = json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def register_equity_claims(app):
    from flask import Response, jsonify, request

    @app.get('/api/equity-claims/status')
    def equity_claims_status_api():
        """Operational state of the internal claims dependency; never a secret."""
        return jsonify(
            binding=BINDING_NAME,
            configured=service_binding() is not None,
            service_credential_configured=bool(provider_setting(SERVICE_TOKEN_SETTING)),
            caller=configured_caller(),
            caller_approved=configured_caller() == SERVICE_CALLER,
            route=CLAIMS_PATH,
            adapter_version=ADAPTER_VERSION,
            credentials_exposed=False,
            note=('A service binding keeps this dependency inside the account. Configuration '
                  'does not certify that any filer or release is materialized.'),
        )

    @app.post('/api/equity-claims/bridge')
    def equity_claims_bridge_api():
        try:
            raw = request.get_json(silent=True)
            if not isinstance(raw, dict):
                raise ValueError('Send financials, valuation_date, cik and explicit assumptions.')
            from app import provider_value, resolve_benchmark_selections
            from enterprise_valuation import value_enterprise

            cik = raw.get('cik')
            if not isinstance(cik, str) or not re.fullmatch(r'\d{10}', cik):
                raise ValueError('An explicit ten-digit CIK is required.')
            valuation_date = raw.get('valuation_date')
            iso_date(valuation_date, 'Valuation date')
            symbol = ticker_symbol(raw.get('ticker'))
            selected = resolve_benchmark_selections(raw.get('benchmark_selections'), valuation_date)
            # The enterprise value is recomputed here from the attested bundle; a
            # client-supplied enterprise value is never accepted.
            enterprise = value_enterprise(
                raw.get('financials'), selected, raw.get('revenue_growth_rates'),
                raw.get('terminal_growth'), raw.get('terminal_roic'),
                valuation_date=valuation_date, suitable=raw.get('suitable'),
                evidence_secret=provider_value('ZION_HISTORY_TOKEN'))
            source_asof = raw.get('source_asof')
            if source_asof is not None:
                iso_date(source_asof, 'Evidence cutoff')
            expected_source_release_id = raw.get('expected_source_release_id')
            if expected_source_release_id is not None and not re.fullmatch(
                    r'[0-9a-f]{64}', str(expected_source_release_id)):
                raise ValueError('expected_source_release_id must be a 64-character hex release id.')
            record = bridge_scenario(
                symbol, valuation_date, cik=cik,
                enterprise_value=enterprise['enterprise_value'],
                expected_release_id=raw.get('expected_release_id'),
                preferred_terms=raw.get('preferred_terms'),
                scenario=raw.get('scenario', 'AS_CONVERTED_MAX_RATE'),
                noncontrolling_policy=raw.get('noncontrolling_policy', 'DEDUCT_REPORTED'),
                source_asof=source_asof,
                expected_source_release_id=expected_source_release_id)
            record['enterprise_scenario'] = {
                'schema_version': enterprise.get('schema_version'),
                'model_version': enterprise.get('model_version'),
                'status': enterprise.get('status'),
                'enterprise_value': enterprise.get('enterprise_value'),
                'financial_cutoff': enterprise.get('financial_cutoff'),
                'analyst_assumptions': enterprise.get('analyst_assumptions'),
                'benchmark_assumptions': enterprise.get('benchmark_assumptions'),
                'warnings': enterprise.get('warnings'),
                'source': enterprise.get('source'),
            }
            return jsonify(save_bridge(record)), 201
        except ProviderError as exc:
            return jsonify(error=str(exc)), 503
        except (ValueError, TypeError, KeyError) as exc:
            return jsonify(error=str(exc)), 400

    @app.get('/api/equity-claims/bridges')
    def equity_claims_bridges_api():
        try:
            return jsonify(list_bridges(request.args.get('ticker')))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

    @app.get('/api/equity-claims/bridges/<identity>')
    def equity_claims_bridge_detail_api(identity):
        record = get_bridge(identity)
        return jsonify(record) if record else (jsonify(error='Bridge record not found.'), 404)

    @app.get('/api/equity-claims/bridges/<identity>/export/json')
    def equity_claims_bridge_export(identity):
        record = get_bridge(identity)
        if not record:
            return jsonify(error='Bridge record not found.'), 404
        response = Response(json.dumps(record, indent=1, sort_keys=True),
                            mimetype='application/json')
        response.headers['Content-Disposition'] = (
            f'attachment; filename="{record["ticker"]}-equity-claims-{record["id"]}.json"')
        return response
