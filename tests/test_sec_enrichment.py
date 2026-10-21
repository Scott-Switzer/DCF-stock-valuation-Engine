from sec_enrichment import recent_claims


def facts(rows):
    return {'cik': 1, 'facts': {'us-gaap': {tag: {'units': {'shares' if 'Shares' in tag else 'USD': values}} for tag, values in rows.items()}}}


def row(value, **extra):
    return {'val': value, 'end': '2026-06-30', 'filed': '2026-08-01', 'accn': 'filing-one', 'form': '10-Q', **extra}


def test_recent_claims_do_not_fill_absent_debt_or_preferred_with_zero():
    p = recent_claims(facts({'Assets': [row(100)], 'LongTermDebtCurrent': [row(5)]}), '0000000001', '2026-10-15', {})
    assert p['fields']['short_term_debt'] is None
    assert p['fields']['preferred_equity'] is None
    assert 'MISSING_SHORT_TERM_DEBT' in p['gaps']


def test_latest_balance_context_blocks_cross_filing_and_future_observations():
    p = recent_claims(facts({'Assets': [row(100)], 'CashAndCashEquivalentsAtCarryingValue': [row(8, accn='other'), row(9, filed='2026-10-20')]}), '0000000001', '2026-10-15', {})
    assert p['fields']['cash'] is None


def test_only_explicit_same_filing_components_derive_zero_and_split_debt():
    p = recent_claims(facts({'Assets': [row(100)], 'StockholdersEquity': [row(40)], 'CommonStockEquity': [row(40)], 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest': [row(43)], 'LongTermDebtCurrent': [row(5)], 'ShortTermBorrowings': [row(2)], 'LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities': [row(25)]}), '0000000001', '2026-10-15', {})
    assert p['fields']['preferred_equity']['value'] == 0
    assert p['fields']['minority_interest']['value'] == 3
    assert p['fields']['short_term_debt']['value'] == 7
    assert p['fields']['long_term_debt']['value'] == 20


def test_quarter_shares_are_not_annualized_or_labeled_spot():
    p = recent_claims(facts({'Assets': [row(100)], 'WeightedAverageNumberOfDilutedSharesOutstanding': [row(10, start='2026-01-01'), row(11, start='2026-04-01')]}), '0000000001', '2026-10-15', {})
    assert p['fields']['diluted_shares']['value'] == 11
    assert 'NOT_SPOT' in p['share_basis']


def test_component_notes_and_unspecified_debt_do_not_prove_noncurrent_total():
    p = recent_claims(facts({'Assets': [row(100)], 'LongTermDebtCurrent': [row(5)], 'LongTermDebt': [row(25)], 'LongTermNotesPayable': [row(20)]}), '0000000001', '2026-10-15', {})
    assert p['fields']['long_term_debt'] is None


def test_ifrs_source_is_an_adapter_gap_not_missing_source():
    p = recent_claims({'cik': 1, 'facts': {'ifrs-full': {'Assets': {}}}}, '0000000001', '2026-10-15', {})
    assert p['gaps'] == ['IFRS_ACCOUNTING_ADAPTER_REQUIRED']
