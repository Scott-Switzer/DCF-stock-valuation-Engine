from datetime import date

import pytest

from scripts.public_sec_equity_bridge import (
    build_components,
    build_receipt,
    debt_and_lease_claims,
    equity_per_share,
    nonoperating_assets,
    pit_instant,
    preferred_terms_scenarios,
    share_count,
)

ASOF = date(2026, 10, 14)


def fact(val, end, filed, form='10-Q', accn='0000000000-26-000001', **extra):
    row = dict(val=val, end=end, filed=filed, form=form, accn=accn)
    row.update(extra)
    return row


def companyfacts(**concepts):
    return {'us-gaap': {name: {'units': {'USD': rows}} for name, rows in concepts.items()},
            'dei': {}}


def test_filing_after_valuation_date_is_not_eligible():
    facts = companyfacts(CashAndCashEquivalentsAtCarryingValue=[
        fact(100, '2026-06-30', '2026-07-29'),
        fact(999, '2026-09-30', '2026-10-30'),  # filed after the valuation date
    ])
    picked = pit_instant(facts, 'CashAndCashEquivalentsAtCarryingValue', ASOF)
    assert picked['value'] == 100 and picked['filed'] == '2026-07-29'


def test_latest_period_wins_then_latest_filing_for_that_period():
    facts = companyfacts(CashAndCashEquivalentsAtCarryingValue=[
        fact(100, '2026-06-30', '2026-07-01', accn='a'),
        fact(105, '2026-06-30', '2026-08-01', accn='b'),  # amendment for same period
    ])
    picked = pit_instant(facts, 'CashAndCashEquivalentsAtCarryingValue', ASOF)
    assert picked['value'] == 105 and picked['accession'] == 'b'


def test_facts_older_than_staleness_cap_are_not_current():
    facts = companyfacts(CommercialPaper=[fact(0, '2025-06-30', '2025-07-30', form='10-K')])
    assert pit_instant(facts, 'CommercialPaper', ASOF) is None


def test_duration_and_segment_facts_are_excluded():
    facts = companyfacts(LongTermDebtCurrent=[
        fact(50, '2026-06-30', '2026-07-01', start='2025-07-01'),
        fact(60, '2026-06-30', '2026-07-01', segment={'dim': 'x'}),
    ])
    assert pit_instant(facts, 'LongTermDebtCurrent', ASOF) is None


def test_microsoft_style_lease_total_is_not_double_counted():
    facts = companyfacts(
        LongTermDebtCurrent=[fact(9, '2026-06-30', '2026-07-29', form='10-K')],
        LongTermDebtNoncurrent=[fact(31, '2026-06-30', '2026-07-29', form='10-K')],
        LongTermDebt=[fact(40, '2026-06-30', '2026-07-29', form='10-K')],
        FinanceLeaseLiability=[fact(66, '2026-06-30', '2026-07-29', form='10-K')],
        FinanceLeaseLiabilityCurrent=[fact(5, '2026-06-30', '2026-07-29', form='10-K')],
        FinanceLeaseLiabilityNoncurrent=[fact(61, '2026-06-30', '2026-07-29', form='10-K')],
    )
    comp = build_components(facts, ASOF)
    debt, notes = debt_and_lease_claims(comp)
    # components 40 + lease total 66 = 106; the lease parts must not be added again.
    assert debt == 106
    assert notes == []


def test_lease_parts_are_used_only_when_total_is_absent():
    facts = companyfacts(
        LongTermDebtCurrent=[fact(1, '2026-06-30', '2026-07-01')],
        FinanceLeaseLiabilityCurrent=[fact(2, '2026-06-30', '2026-07-01')],
        FinanceLeaseLiabilityNoncurrent=[fact(3, '2026-06-30', '2026-07-01')],
    )
    debt, _ = debt_and_lease_claims(build_components(facts, ASOF))
    assert debt == 1 + 2 + 3


def test_period_mismatch_between_total_and_components_is_reported_not_netted():
    facts = companyfacts(
        LongTermDebtCurrent=[fact(1, '2026-06-30', '2026-07-01')],
        LongTermDebtNoncurrent=[fact(2, '2026-06-30', '2026-07-01')],
        LongTermDebt=[fact(99, '2025-12-31', '2026-02-05', form='10-K')],
    )
    debt, notes = debt_and_lease_claims(build_components(facts, ASOF))
    assert debt == 3
    assert any('different period' in n for n in notes)


def test_absent_preferred_and_minority_are_labelled_assumed_absent():
    facts = companyfacts(CashAndCashEquivalentsAtCarryingValue=[fact(10, '2026-06-30', '2026-07-01')])
    comp = build_components(facts, ASOF)
    result = equity_per_share(100.0, comp, dict(value=5.0), 0, nonoperating_assets(comp))
    assert result['claim_statuses'] == {'PreferredStockValue': 'NOT_REPORTED_ASSUMED_ABSENT',
                                        'MinorityInterest': 'NOT_REPORTED_ASSUMED_ABSENT'}
    assert result['value_per_share'] == pytest.approx((100.0 + 10.0) / 5.0)


def test_share_count_prefers_cover_page_then_balance_sheet_all_classes():
    dei_only = {'us-gaap': {}, 'dei': {'EntityCommonStockSharesOutstanding': {'units': {'shares': [
        dict(val=7, end='2026-07-17', filed='2026-07-31', form='10-Q', accn='x')]}}}}
    assert share_count(dei_only, ASOF)['basis'] == 'COVER_PAGE_DEI'
    balance_only = {'us-gaap': {'CommonStockSharesOutstanding': {'units': {'shares': [
        dict(val=12, end='2026-06-30', filed='2026-07-23', form='10-Q', accn='y')]}}}, 'dei': {}}
    assert share_count(balance_only, ASOF)['basis'] == 'BALANCE_SHEET_ALL_CLASSES'
    assert share_count({'us-gaap': {}, 'dei': {}}, ASOF) is None


def test_nonoperating_assets_use_short_term_or_current_securities_not_both():
    facts = companyfacts(
        CashAndCashEquivalentsAtCarryingValue=[fact(10, '2026-06-30', '2026-07-01')],
        ShortTermInvestments=[fact(20, '2026-06-30', '2026-07-01')],
        MarketableSecuritiesCurrent=[fact(30, '2026-06-30', '2026-07-01')],
        MarketableSecuritiesNoncurrent=[fact(40, '2026-06-30', '2026-07-01')],
    )
    assert nonoperating_assets(build_components(facts, ASOF)) == 10 + 20 + 40


COVER_SHARES = {'EntityCommonStockSharesOutstanding': {'units': {'shares': [
    dict(val=12_230_000_000, end='2026-07-17', filed='2026-07-23', form='10-Q', accn='x')]}}}


def test_noncontrolling_interest_falls_back_to_the_vie_disclosure():
    """Alphabet files only the VIE disclosure; it is the claim and must be deducted once."""
    facts = companyfacts(
        CashAndCashEquivalentsAtCarryingValue=[fact(100, '2026-06-30', '2026-07-23')],
        NoncontrollingInterestInVariableInterestEntity=[fact(7_100_000_000, '2026-06-30', '2026-07-23')],
    )
    result = equity_per_share(2_179_137_903_112.5725,
                             build_components(facts, ASOF),
                             dict(value=12_230_000_000.0),
                             102_754_000_000, 242_474_000_000)
    assert result['preferred_and_minority_claims']['MinorityInterest'] == 7_100_000_000
    assert result['claim_statuses']['MinorityInterest'] == 'REPORTED_VIA_VIE_DISCLOSURE'
    assert result['minority_interest']['source_concept'] == 'NoncontrollingInterestInVariableInterestEntity'
    assert result['minority_interest']['row']['accession'] == '0000000000-26-000001'
    # The same claims as the attested contract path: enterprise + nonoperating - debt - NCI.
    assert result['common_equity_value'] == pytest.approx(2_311_757_903_112.5725)
    assert result['value_per_share'] == pytest.approx(2_311_757_903_112.5725 / 12_230_000_000.0)


def test_reported_total_is_used_and_never_summed_with_the_vie_disclosure():
    facts = companyfacts(
        CashAndCashEquivalentsAtCarryingValue=[fact(100, '2026-06-30', '2026-07-23')],
        MinorityInterest=[fact(8_000_000_000, '2026-06-30', '2026-07-23')],
        NoncontrollingInterestInVariableInterestEntity=[fact(7_100_000_000, '2026-06-30', '2026-07-23')],
    )
    result = equity_per_share(1000.0, build_components(facts, ASOF), dict(value=5.0), 0, 100.0)
    assert result['preferred_and_minority_claims']['MinorityInterest'] == 8_000_000_000
    assert result['claim_statuses']['MinorityInterest'] == 'REPORTED'
    assert result['minority_interest']['vie_row']['value'] == 7_100_000_000
    assert result['value_per_share'] == pytest.approx((1000.0 + 100.0 - 8_000_000_000) / 5.0)

GOOGL_TERMS = {'series': [
    dict(name='A', depositary_shares=192_500_000, depositary_per_preferred=20,
         liquidation_preference_per_share=1000, min_rate_per_preferred=2.2520, max_rate_per_preferred=2.8160),
    dict(name='B', depositary_shares=192_500_000, depositary_per_preferred=20,
         liquidation_preference_per_share=1000, min_rate_per_preferred=2.2740, max_rate_per_preferred=2.8420),
]}


def test_preferred_scenarios_use_offering_terms_and_never_double_count():
    shares = dict(value=12_230_000_000.0)
    s = preferred_terms_scenarios(GOOGL_TERMS, 2_318_800_000_000.0, shares)
    assert s['preferred_shares'] == pytest.approx(19_250_000)
    assert s['liquidation_preference_total'] == pytest.approx(19_250_000_000)
    max_added = 9_625_000 * 2.8160 + 9_625_000 * 2.8420
    assert s['as_converted_max_rate']['shares_added'] == pytest.approx(max_added)
    assert s['as_converted_max_rate']['claim'] == 0.0
    assert s['as_converted_max_rate']['value_per_share'] == pytest.approx(
        2_318_800_000_000.0 / (12_230_000_000.0 + max_added))
    assert s['as_converted_min_rate']['shares_added'] < max_added
    assert s['liquidation_preference_claim']['shares_added'] == 0.0


def test_receipt_with_preferred_terms_replaces_assumed_absent_claim():
    facts = companyfacts(CashAndCashEquivalentsAtCarryingValue=[fact(100, '2026-06-30', '2026-07-23')])
    facts['us-gaap']['PreferredStockSharesOutstanding'] = {'units': {'shares': [
        fact(19_000_000, '2026-06-30', '2026-07-23')]}}
    facts['dei'] = {'EntityCommonStockSharesOutstanding': {'units': {'shares': [
        dict(val=12_230_000_000, end='2026-07-17', filed='2026-07-23', form='10-Q', accn='x')]}}}
    enterprise = dict(enterprise_value=1000.0, valuation_date='2026-10-14',
                      analyst_assumptions={})
    receipt = build_receipt('GOOGL', facts, enterprise, ASOF, preferred_terms=GOOGL_TERMS)
    assert receipt['preferred']['primary'] == 'as_converted_max_rate'
    assert receipt['preferred']['legacy_assumed_absent_value_per_share'] == pytest.approx(1100.0 / 12_230_000_000.0)
    assert receipt['preferred']['reported_shares_outstanding']['value'] == 19_000_000


def test_preferred_terms_fail_closed_when_reported_carrying_amount_exists():
    facts = companyfacts(PreferredStockValue=[fact(18_023_000_000, '2026-06-30', '2026-07-23')])
    facts['dei'] = COVER_SHARES
    enterprise = dict(enterprise_value=1000.0, valuation_date='2026-10-14', analyst_assumptions={})
    with pytest.raises(ValueError, match='PreferredStockValue is reported'):
        build_receipt('GOOGL', facts, enterprise, ASOF, preferred_terms=GOOGL_TERMS)


def test_preferred_terms_fail_closed_when_reported_share_count_conflicts():
    facts = companyfacts()
    facts['dei'] = COVER_SHARES
    facts['us-gaap']['PreferredStockSharesOutstanding'] = {'units': {'shares': [
        fact(12_000_000, '2026-06-30', '2026-07-23')]}}
    enterprise = dict(enterprise_value=1000.0, valuation_date='2026-10-14', analyst_assumptions={})
    with pytest.raises(ValueError, match='conflict with terms'):
        build_receipt('GOOGL', facts, enterprise, ASOF, preferred_terms=GOOGL_TERMS)
