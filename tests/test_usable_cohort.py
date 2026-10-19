import pytest
from scripts.verify_usable_cohort import account_cohort


def test_cohort_continues_after_failure_and_accounts_for_each_issuer():
    rows = [{'cik':'0000000001'}, {'cik':'0000000002'}]
    def evaluate(row):
        if row['cik'].endswith('1'):
            raise TimeoutError('a sensitive upstream message')
        return dict(cik=row['cik'], status='BLOCKED', blockers=['DATED_ASSUMPTIONS_REQUIRED'])
    report = account_cohort(rows, evaluate)
    assert report['selected'] == report['accounted'] == 2
    assert report['results'][0]['blockers'] == ['TRANSPORT_OR_INPUT_FAILURE:TimeoutError']
    assert 'sensitive' not in str(report)


def test_duplicate_issuers_fail_before_evaluation():
    with pytest.raises(ValueError, match='distinct'):
        account_cohort([{'cik':'0000000001'}]*2, lambda row: row)


def test_wrong_result_identity_is_a_blocker():
    report = account_cohort([{'cik':'0000000001'}], lambda row: {'cik':'0000000002'})
    assert report['results'][0]['status'] == 'BLOCKED'


def test_standard_scenario_requires_explicit_forecasts_and_retains_benchmark_pins():
    from scripts.verify_usable_cohort import standard_scenario
    prepared={'request_template':{'cik':'0000320193','financials':{'source':{'release_id':'a'*64}}},
              'benchmark_references':{'wacc':{'release_id':'b'*64,'measure':'wacc'}}}
    with pytest.raises(ValueError,match='explicit'):
        standard_scenario(prepared,industry='Total Market',valuation_date='2026-10-15',
                          growth=None,terminal_growth=.02,terminal_roic=.15)
    body=standard_scenario(prepared,industry='Total Market',valuation_date='2026-10-15',
                           growth=.05,terminal_growth=.02,terminal_roic=.15)
    assert body['revenue_growth_rates']==[.05]*5
    assert body['benchmark_selections']['wacc']['release_id']=='b'*64
    assert body['financials']==prepared['request_template']['financials']
