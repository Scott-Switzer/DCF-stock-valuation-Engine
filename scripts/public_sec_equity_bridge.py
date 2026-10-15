"""Point-in-time enterprise-to-equity bridge from SEC public Company Facts.

This is NOT Zion-attested evidence. Balance-sheet claims come from the public SEC
companyfacts API and are selected point-in-time: only facts filed on or before the
valuation date are eligible, the latest period end wins, and facts older than
MAX_AGE_DAYS before the valuation date are treated as not current. Every component
keeps its concept, period end, form, accession and filing date.

Policies (explicit and assumption-dependent):
- Debt = LongTermDebtCurrent + LongTermDebtNoncurrent + current borrowings
  (CommercialPaper, ShortTermBorrowings, OtherShortTermBorrowings) when current.
  The LongTermDebt total is used only when both debt components are absent, and
  any disagreement with the component sum is recorded.
- Finance leases: FinanceLeaseLiability total when reported, otherwise current +
  noncurrent. Operating leases are excluded, consistent with EBIT including
  operating lease cost.
- Nonoperating assets = cash and equivalents + short-term investments (or current
  marketable securities) + noncurrent marketable securities. Long-term equity
  investments are excluded.
- PreferredStockValue and MinorityInterest that are absent from companyfacts are
  assumed absent and labelled, never presented as reviewed zeros.
- Shares: dei:EntityCommonStockSharesOutstanding (cover page) when reported;
  otherwise the all-class balance-sheet CommonStockSharesOutstanding.
"""

import argparse
import json
from datetime import date, timedelta

MAX_AGE_DAYS = 400
DEBT_COMPONENTS = ('LongTermDebtCurrent', 'LongTermDebtNoncurrent')
CURRENT_BORROWINGS = ('CommercialPaper', 'ShortTermBorrowings', 'OtherShortTermBorrowings')
LEASE_TOTAL = 'FinanceLeaseLiability'
LEASE_PARTS = ('FinanceLeaseLiabilityCurrent', 'FinanceLeaseLiabilityNoncurrent')
CASH = 'CashAndCashEquivalentsAtCarryingValue'
SHORT_INVESTMENTS = ('ShortTermInvestments', 'MarketableSecuritiesCurrent')
NONCURRENT_SECURITIES = 'MarketableSecuritiesNoncurrent'
CLAIMS = ('PreferredStockValue', 'MinorityInterest')


def pit_instant(facts, concept, valuation_date, unit='USD', taxonomy='us-gaap'):
    """Latest instant fact filed on/before valuation_date, not older than MAX_AGE_DAYS."""
    body = facts.get(taxonomy, {}).get(concept)
    if not body:
        return None
    rows = body.get('units', {}).get(unit, [])
    floor = valuation_date - timedelta(days=MAX_AGE_DAYS)
    eligible = [
        r for r in rows
        if 'start' not in r and r.get('segment') is None
        and r['filed'] <= valuation_date.isoformat()
        and floor <= date.fromisoformat(r['end']) <= valuation_date
    ]
    if not eligible:
        return None
    end = max(r['end'] for r in eligible)
    row = max((r for r in eligible if r['end'] == end), key=lambda r: r['filed'])
    return dict(concept=concept, value=row['val'], period_end=row['end'], form=row['form'],
                accession=row['accn'], filed=row['filed'], unit=unit)


def build_components(facts, valuation_date):
    """Collect every point-in-time claim component, keyed by XBRL concept."""
    names = (DEBT_COMPONENTS + CURRENT_BORROWINGS + (LEASE_TOTAL,) + LEASE_PARTS + (CASH,)
             + SHORT_INVESTMENTS + (NONCURRENT_SECURITIES, 'LongTermDebt') + CLAIMS)
    comp = {}
    for name in names:
        found = pit_instant(facts, name, valuation_date)
        if found:
            comp[name] = found
    return comp


def debt_and_lease_claims(comp):
    """Non-overlapping debt and lease claims, with the notes that justify each choice."""
    notes = []
    debt_parts = [k for k in DEBT_COMPONENTS + CURRENT_BORROWINGS if k in comp]
    total = sum(comp[k]['value'] for k in debt_parts)
    if not any(k in comp for k in DEBT_COMPONENTS) and 'LongTermDebt' in comp:
        total += comp['LongTermDebt']['value']
        notes.append('LongTermDebt total used because debt components are absent.')
    elif 'LongTermDebt' in comp and any(k in comp for k in DEBT_COMPONENTS):
        period = comp['LongTermDebt']['period_end']
        same = [k for k in DEBT_COMPONENTS if k in comp and comp[k]['period_end'] == period]
        if same and len(same) == len([k for k in DEBT_COMPONENTS if k in comp]):
            gap = comp['LongTermDebt']['value'] - sum(comp[k]['value'] for k in same)
            if gap:
                notes.append(f'LongTermDebt total differs from component sum by {gap} at {period}; components used.')
        else:
            notes.append(f'LongTermDebt total is from {period}, a different period than the components; total ignored.')
    if LEASE_TOTAL in comp:
        total += comp[LEASE_TOTAL]['value']
    else:
        total += sum(comp[k]['value'] for k in LEASE_PARTS if k in comp)
    return total, notes


def nonoperating_assets(comp):
    total = comp[CASH]['value'] if CASH in comp else 0
    total += next((comp[k]['value'] for k in SHORT_INVESTMENTS if k in comp), 0)
    total += comp[NONCURRENT_SECURITIES]['value'] if NONCURRENT_SECURITIES in comp else 0
    return total


def share_count(facts, valuation_date):
    dei = pit_instant(facts, 'EntityCommonStockSharesOutstanding', valuation_date,
                      unit='shares', taxonomy='dei')
    if dei:
        return dict(dei, basis='COVER_PAGE_DEI')
    bs = pit_instant(facts, 'CommonStockSharesOutstanding', valuation_date, unit='shares')
    if bs:
        return dict(bs, basis='BALANCE_SHEET_ALL_CLASSES')
    return None


def equity_per_share(enterprise_value, comp, shares, debt, nonop):
    claims = {k: (comp[k]['value'] if k in comp else 0) for k in CLAIMS}
    statuses = {k: ('REPORTED' if k in comp else 'NOT_REPORTED_ASSUMED_ABSENT') for k in CLAIMS}
    equity = enterprise_value + nonop - debt - sum(claims.values())
    return dict(enterprise_value=enterprise_value, nonoperating_assets=nonop,
                debt_and_lease_claims=debt, preferred_and_minority_claims=claims,
                claim_statuses=statuses, common_equity_value=equity,
                shares_outstanding=shares['value'], value_per_share=equity / shares['value'])


def build_receipt(ticker, facts, enterprise, valuation_date):
    comp = build_components(facts, valuation_date)
    debt, notes = debt_and_lease_claims(comp)
    nonop = nonoperating_assets(comp)
    shares = share_count(facts, valuation_date)
    if shares is None:
        raise ValueError(f'{ticker}: no point-in-time share count; per-share value not computed.')
    result = equity_per_share(enterprise['enterprise_value'], comp, shares, debt, nonop)
    return dict(ticker=ticker, valuation_date=valuation_date.isoformat(),
                source='SEC public companyfacts', attestation='NOT_ZION_ATTESTED',
                enterprise_artifact_valuation_date=enterprise['valuation_date'],
                operating_assumptions=enterprise['analyst_assumptions'],
                components=comp, shares=shares, notes=notes, result=result)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--ticker', required=True)
    parser.add_argument('--companyfacts', required=True)
    parser.add_argument('--enterprise-artifact', required=True)
    parser.add_argument('--valuation-date', required=True)
    parser.add_argument('--output')
    args = parser.parse_args()
    with open(args.companyfacts) as fh:
        facts = json.load(fh)['facts']
    with open(args.enterprise_artifact) as fh:
        enterprise = json.load(fh)['result']
    receipt = build_receipt(args.ticker, facts, enterprise, date.fromisoformat(args.valuation_date))
    text = json.dumps(receipt, indent=1, sort_keys=True)
    if args.output:
        with open(args.output, 'w') as fh:
            fh.write(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
