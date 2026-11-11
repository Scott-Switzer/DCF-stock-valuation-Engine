from copy import deepcopy
import pytest
import research_screen as screen
from app import app
from dcf_loader import ProviderError

@pytest.fixture(autouse=True)
def private_session(monkeypatch):
    monkeypatch.setattr(screen, 'authorized', lambda: True)


PIN = 'a' * 64
PAGE = dict(schema_version='zion-readiness-screen-index-v1', index_id='b'*64,
            release_id='c'*64, engine_release_id=PIN, archive_cutoff='2026-09-24',
            availability_cutoff='2026-09-24T00:00:00Z', qualification='COMPANY_SIDE_ONLY',
            matches=[dict(cik='0000320193', label='Apple', methods=['operating_dcf'],
                          missing=[], share_basis='COVER_PAGE_DEI')], next_cursor=None)


class HTTP:
    def get(self, url, **kw):
        self.url, self.kw = url, kw
        class Response:
            status_code = 200
            content = b'{}'
            def json(self):
                return deepcopy(PAGE)
        return Response()


def test_screen_preserves_source_pins_and_never_invents_ticker():
    transport = HTTP()
    result = screen.load_screen({'method':'operating_dcf', 'limit':'50'}, http=transport,
                                token='secret', base='https://zion.internal')
    assert result['matches'][0]['valuation_blockers'] == ['EXPLICIT_TICKER_REQUIRED', 'DATED_ASSUMPTIONS_REQUIRED']
    assert result['engine_release_id'] == PIN
    assert 'secret' not in str(result)
    assert transport.kw['params']['recipient'] == 'human_research'


@pytest.mark.parametrize('query', [{'limit':'501'}, {'limit':'0'}, {'url':'https://evil.test'},
                                    {'cik':'123'}, {'recipient':'model'}, {'limit':'hello'}])
def test_invalid_queries_fail_before_network(query):
    with pytest.raises(ValueError):
        screen.load_screen(query, http=HTTP(), token='secret', base='https://zion.internal')


def test_source_pin_mismatch_is_refused():
    with pytest.raises(ProviderError, match='index'):
        screen.load_screen({'expected_index_id':'d'*64}, http=HTTP(), token='secret', base='https://zion.internal')


def test_prepare_loads_exact_screen_issuer_and_cutoff(monkeypatch):
    monkeypatch.setattr(screen, 'load_screen', lambda query: deepcopy(PAGE))
    seen = {}
    def load(provider, ticker, asof, **kw):
        seen.update(provider=provider, ticker=ticker, asof=asof, **kw)
        return {'source': {'missing_fields': []}, 'company': {'ticker':ticker}, 'historical':[{'revenue':100,'ebit':20}]}
    monkeypatch.setattr(screen, 'load_document', load)
    response = app.test_client().post('/api/research-screen/prepare', json={
        'ticker':'AAPL', 'cik':'0000320193', 'expected_index_id':'b'*64})
    assert response.status_code == 200
    assert seen['expected_release_id'] == PIN and seen['asof'] == '2026-09-24'
    assert response.json['valuation_blockers'] == ['DATED_ASSUMPTIONS_REQUIRED']
    assert response.json['calculate_endpoint'] == '/api/calculate/enterprise'


def test_prepare_refuses_wrong_issuer(monkeypatch):
    monkeypatch.setattr(screen, 'load_screen', lambda query: deepcopy(PAGE))
    result = app.test_client().post('/api/research-screen/prepare', json={
        'ticker':'MSFT', 'cik':'0000789019', 'expected_index_id':'b'*64})
    assert result.status_code == 409


def test_screen_page_is_integrated():
    response = app.test_client().get('/screen')
    assert response.status_code == 200 and b'Company screening' in response.data


def test_binding_transport_returns_a_decoded_mapping():
    class Binding:
        def get(self, *args, **kwargs):
            return deepcopy(PAGE)
    assert screen.load_screen({}, http=Binding(), token='secret', base='https://zion.internal')['index_id'] == 'b'*64


def test_unauthenticated_screen_is_private(monkeypatch):
    monkeypatch.setattr(screen, 'authorized', lambda: False)
    assert app.test_client().get('/api/research-screen').status_code == 401


def test_prepare_rejects_unverified_ticker_identity(monkeypatch):
    monkeypatch.setattr(screen, 'load_screen', lambda query: deepcopy(PAGE))
    response = app.test_client().post('/api/research-screen/prepare', json={
        'ticker':'MSFT', 'cik':'0000320193', 'expected_index_id':'b'*64})
    assert response.status_code == 409


def test_unused_accounting_fields_are_not_enterprise_blockers(monkeypatch):
    monkeypatch.setattr(screen, 'load_screen', lambda query: deepcopy(PAGE))
    monkeypatch.setattr(screen, 'load_document', lambda *a, **kw: {
        'historical':[{'revenue':100,'ebit':20}],
        'source':{'missing_fields':{'historical.2025-09-27.d_and_a':'NO_MAPPING','market.price':'NO_MAPPING'}}})
    result = app.test_client().post('/api/research-screen/prepare', json={
        'ticker':'AAPL','cik':'0000320193','expected_index_id':'b'*64})
    assert result.json['valuation_blockers'] == ['DATED_ASSUMPTIONS_REQUIRED']
    assert 'market.price' in result.json['source_missing_fields']


def test_current_sec_alias_can_prepare_issuer_research_without_certifying_history(monkeypatch):
    monkeypatch.setattr(screen, 'load_screen', lambda query: deepcopy(PAGE))
    monkeypatch.setattr(screen, 'issuer_identity', lambda *a: {
        'status':'CURRENT_SEC_ALIAS_ONLY', 'historical_security_eligible':False,
        'cik':'0000320193','ticker':'AAPL'})
    monkeypatch.setattr(screen, 'load_document', lambda *a, **kw: {
        'historical':[{'revenue':100,'ebit':20}], 'source':{'missing_fields':{}}})
    response = app.test_client().post('/api/research-screen/prepare',json={
        'ticker':'AAPL','cik':'0000320193','expected_index_id':'b'*64})
    assert response.status_code == 200
    assert response.json['issuer_identity']['historical_security_eligible'] is False


def test_sec_submissions_alias_is_checked_against_requested_issuer(monkeypatch):
    # The live SEC submissions alias check is a local-development direct
    # path; in production the gate leaves unreviewed aliases unverified.
    monkeypatch.setenv("DCF_ALLOW_DIRECT_FETCH", "1")
    class HTTP:
        def get(self,*a,**kw):
            return {'cik':320193,'name':'Apple Inc.','tickers':['AAPL']}
    result=screen.issuer_identity('AAPL','0000320193','2020-01-01',http=HTTP())
    assert result['historical_security_eligible'] is False
    assert result['status']=='CURRENT_SEC_ALIAS_ONLY'
    assert screen.issuer_identity('MSFT','0000320193','2020-01-01',http=HTTP()) is None
