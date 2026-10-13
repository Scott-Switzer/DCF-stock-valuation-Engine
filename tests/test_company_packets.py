import json
from copy import deepcopy
from pathlib import Path
import pytest
import company_packets as cp
from dcf_loader import ProviderError


class Store:
    def __init__(self): self.values = {}; self.writes = 0
    def get(self, key): return self.values.get(key)
    def set(self, key, value, ttl): self.values[key] = value; self.writes += 1


@pytest.fixture
def bundle():
    return {'financials': json.loads(Path('data/demo.json').read_text()), 'load_summary': {'elapsed_seconds': 9}}


def loader_for(bundle, calls):
    def loader(method, ticker, asof, *args):
        calls.append((method, ticker, asof))
        b = deepcopy(bundle); b['financials']['company']['ticker'] = ticker; b['financials']['valuation_date'] = asof
        return b
    return loader


def test_cache_hit_preserves_dates_and_isolates_mutation(bundle):
    store, calls = Store(), []
    loader = loader_for(bundle, calls)
    first = cp.load_cached_method('dcf', 'MSFT', '2026-10-10', store=store, loader=loader, clock=lambda: 1000)
    original_price = first['financials']['market']['price']
    first['financials']['market']['price'] = 1
    second = cp.load_cached_method('dcf', 'MSFT', '2026-10-10', store=store, loader=loader, clock=lambda: 1010)
    assert len(calls) == 1
    assert second['financials']['market']['price'] == original_price
    assert second['financials']['market']['price_as_of'] == bundle['financials']['market']['price_as_of']
    assert second['load_summary']['assembly_cache']['state'] == 'HIT'
    assert second['load_summary']['original_assembly_seconds'] == 9
    assert second['load_summary']['elapsed_seconds'] < 9


@pytest.mark.parametrize('change', ['expired', 'corrupt', 'ticker', 'date', 'method', 'custom'])
def test_cache_cannot_cross_identity_or_custom_assumptions(bundle, change):
    store, calls = Store(), []; loader = loader_for(bundle, calls)
    cp.load_cached_method('dcf', 'MSFT', '2026-10-10', store=store, loader=loader, clock=lambda: 1000)
    method, ticker, asof, erp, now = 'dcf', 'MSFT', '2026-10-10', .05, 1010
    if change == 'expired': now = 1300
    elif change == 'corrupt': next(iter(store.values.values()))['bundle']['financials']['market']['price'] = 1
    elif change == 'ticker': ticker = 'AAPL'
    elif change == 'date': asof = '2026-10-09'
    elif change == 'method': method = 'ddm'
    else: erp = .06
    cp.load_cached_method(method, ticker, asof, erp, store=store, loader=loader, clock=lambda: now)
    assert len(calls) == 2


def test_failures_and_user_documents_are_not_cached(bundle):
    store = Store()
    def fail(*args): raise ProviderError('Missing operating income')
    with pytest.raises(ProviderError): cp.load_cached_method('dcf', 'JPM', store=store, loader=fail)
    assert store.writes == 0
    with pytest.raises(TypeError): cp.load_cached_method('dcf', 'MSFT', snapshot=bundle)


def test_bad_cache_falls_back_to_loader(bundle):
    class Broken(Store):
        def get(self, key): raise RuntimeError()
        def set(self, *args): raise RuntimeError()
    calls = []
    r = cp.load_cached_method('dcf', 'MSFT', store=Broken(), loader=loader_for(bundle, calls))
    assert len(calls) == 1 and r['financials']


def test_packet_provenance_readiness_and_missing_components(bundle):
    # Synthetic fixture remains explicitly unverified, never falsely certified.
    packet = cp.assemble_packet(bundle)
    assert packet['independent_source_verification'] == 'NOT_ESTABLISHED'
    assert len(packet['peer_candidates']['tickers']) == 4
    assert not packet['peer_candidates']['reviewed']
    assert packet['components']['analysts'] == 'NOT_CACHED'
    price = next(x for x in packet['fields'] if x['field'] == 'market.price')
    assert price['unit'] == 'USD/share'
    assert not price['independently_source_verified']
    assert any(x['code'] == 'synthetic_data' for x in packet['issues'])
    assert all(not x['mapped'] for x in packet['datasets'] if x['dataset'] == 'private_wrds')


def test_wrong_identity_and_foreign_analysts_rejected(bundle):
    with pytest.raises(ValueError): cp.assemble_packet(bundle, ticker='ZZZZ')
    p = cp.assemble_packet(bundle, analysts={'ticker': 'ZZZZ'})
    assert p['analyst_reference'] is None


def test_blocked_company_is_retained_in_ledger():
    p = cp.assemble_packet(None, ticker='JPM', asof='2026-10-10', error='Missing operating income')
    assert p['status'] == 'BLOCKED' and p['ticker'] == 'JPM'
    assert p['fields'] == [] and p['reason'] == 'Missing operating income'


def test_freshness_does_not_confuse_retrieval_with_observation():
    assert cp.age_status('2020-01-01', '2026-10-10', 550)['status'] == 'STALE'
    assert cp.age_status(None, '2026-10-10', 550)['status'] == 'UNKNOWN'
    assert cp.age_status('2026-10-11', '2026-10-10', 7)['status'] == 'FUTURE'


def test_packet_route_validates_queries(monkeypatch):
    from app import app
    monkeypatch.setattr(cp, 'load_company_packet', lambda ticker, asof: {'ticker': ticker, 'status': 'BLOCKED'})
    with app.test_client() as client:
        assert client.get('/api/company/MSFT/packet').json['ticker'] == 'MSFT'
        assert client.get('/api/company/MSFT/packet?as_of=2026-10-10&as_of=2026-10-09').status_code == 400
        assert client.get('/api/company/MSFT/packet?secret=x').status_code == 400


def test_analysts_require_issuer_currency_and_nonfuture_reference_date(bundle):
    ticker = bundle['financials']['company']['ticker']
    asof = bundle['financials']['valuation_date']
    ref = {'source_url': f'https://finance.yahoo.com/quote/{ticker}/analysis/', 'currency': 'USD', 'retrieved_at': asof}
    assert cp.assemble_packet(bundle, analysts=ref)['analyst_reference'] == ref
    ref['retrieved_at'] = '2099-01-01'
    assert cp.assemble_packet(bundle, analysts=ref)['analyst_reference'] is None


def test_prior_annual_periods_are_historical_not_stale(bundle):
    packet = cp.assemble_packet(bundle)
    latest = max(r['period_end'] for r in bundle['financials']['historical'])
    older = [r for r in packet['fields'] if r['field'].startswith('historical.') and r['period_end'] < latest]
    assert older and all(r['freshness']['status'] == 'HISTORICAL' for r in older)


def test_coverage_page_renders_blocked_company_without_hiding_it(monkeypatch):
    from app import app
    monkeypatch.setattr(cp, 'load_company_packet', lambda ticker: cp.assemble_packet(None, ticker=ticker, error='Missing inputs'))
    with app.test_client() as client:
        r = client.get('/coverage/JPM')
        assert r.status_code == 200 and 'Missing inputs' in r.text and 'JPM coverage' in r.text


def test_exact_fiscal_year_end_does_not_make_latest_row_historical(bundle):
    from datetime import date, timedelta
    doc = bundle['financials']
    latest = max(x['period_end'] for x in doc['historical'])
    exact = (date.fromisoformat(latest) - timedelta(days=3)).isoformat()
    field = f'historical.{latest}.revenue'
    doc['source']['field_coverage'] = [{'field': field, 'period_end': exact, 'available_at': latest, 'status': 'PPE'}]
    p = cp.assemble_packet(bundle)
    receipt = next(x for x in p['fields'] if x['field'] == field)
    assert receipt['period_end'] == exact
    assert receipt['freshness']['status'] != 'HISTORICAL'
    assert receipt['available_at'] == latest
    assert receipt['availability_basis'] == 'FILING_DATE'


def test_baseline_cutoff_is_not_verified_availability(bundle):
    p = cp.assemble_packet(bundle)
    receipt = next(x for x in p['fields'] if x['field'] == 'market.price')
    assert receipt['available_at'] is None
    assert receipt['availability_basis'] == 'NOT_ESTABLISHED'
    assert 'reported_available_at' in receipt


def test_disk_failure_preserves_previous_ledger_checkpoint(tmp_path, monkeypatch):
    from scripts import build_company_ledger as ledger
    target = tmp_path / 'report.json'; target.write_text('{"previous":true}')
    def disk_full(value, stream, **kwargs):
        stream.write('{"partial":')
        raise OSError(28, 'No space left on device')
    monkeypatch.setattr(ledger.json, 'dump', disk_full)
    with pytest.raises(OSError): ledger.write_json_atomic(target, {'next': True})
    assert json.loads(target.read_text()) == {'previous': True}
    assert list(tmp_path.iterdir()) == [target]
