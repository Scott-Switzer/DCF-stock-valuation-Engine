from datetime import date

import pytest

from scripts.public_sec_equity_bridge import (
    build_components,
    debt_and_lease_claims,
    equity_per_share,
    nonoperating_assets,
    pit_instant,
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
