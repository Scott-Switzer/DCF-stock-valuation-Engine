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
- PreferredStockValue, MinorityInterest and the noncontrolling interest in variable
  interest entities are each a claim on the consolidated cash flows the enterprise value
  measures, and each is deducted exactly once. The noncontrolling interest total is used
  when the filer files it, otherwise the VIE disclosure is used, never both. A claim
  absent from companyfacts is assumed absent and labelled, never presented as a reviewed
  zero.
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
NCI_VIE = 'NoncontrollingInterestInVariableInterestEntity'


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
             + SHORT_INVESTMENTS + (NONCURRENT_SECURITIES, 'LongTermDebt') + CLAIMS + (NCI_VIE,))
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


def minority_claim(comp):
    """The noncontrolling interest: the filed total, else the VIE disclosure, never both.

    A filer that binds the minority result into one company often files only
    us-gaap:NoncontrollingInterestInVariableInterestEntity, and that disclosure is itself
    the claim. When both are filed the VIE amount is normally a subset of the total, so
    the total is used and the VIE row is carried as evidence instead of being added.
    """
    for concept in ('MinorityInterest', NCI_VIE):
        if concept in comp:
            return comp[concept]['value'], concept
    return None, None


def equity_per_share(enterprise_value, comp, shares, debt, nonop):
    minority, source = minority_claim(comp)
    zero = (comp['PreferredStockValue']['value'] if 'PreferredStockValue' in comp else 0)
    claims = {'PreferredStockValue': zero, 'MinorityInterest': minority if minority is not None else 0}
    statuses = {k: ('REPORTED' if k in comp else 'NOT_REPORTED_ASSUMED_ABSENT') for k in CLAIMS}
    if minority is not None and source != 'MinorityInterest':
        statuses['MinorityInterest'] = 'REPORTED_VIA_VIE_DISCLOSURE'
    equity = enterprise_value + nonop - debt - sum(claims.values())
    minority_evidence = dict(source_concept=source, row=comp.get(source) if source else None,
                             vie_row=comp.get(NCI_VIE) if source == 'MinorityInterest' else None,
                             rule='Deducted once: the filed total when present, otherwise the '
                                  'VIE disclosure; the two are never summed.')
    return dict(enterprise_value=enterprise_value, nonoperating_assets=nonop,
                debt_and_lease_claims=debt, preferred_and_minority_claims=claims,
                claim_statuses=statuses, minority_interest=minority_evidence,
                common_equity_value=equity,
                shares_outstanding=shares['value'], value_per_share=equity / shares['value'])


PREFERRED_SHARE_ROUNDING_TOLERANCE = 500_000  # XBRL preferred counts are rounded to millions


def preferred_terms_scenarios(terms, equity_before_preferred, shares):
    """Scenarios for mandatory convertible preferred, built from offering terms.

    Per-preferred-share conversion rates come from the offering documents, not companyfacts.
    As-converted scenarios add converted common shares and deduct no preferred claim, so the
    instrument is never counted both as a claim and as converted shares. The liquidation
    scenario deducts the preference and adds no shares; it is a sensitivity, not the
    mandatory-conversion economics.
    """
    count = {}
    for s in terms['series']:
        count[s['name']] = s['depositary_shares'] / s['depositary_per_preferred']
    preferred = sum(count.values())
    liquidation = sum(count[s['name']] * s['liquidation_preference_per_share'] for s in terms['series'])
    min_added = sum(count[s['name']] * s['min_rate_per_preferred'] for s in terms['series'])
    max_added = sum(count[s['name']] * s['max_rate_per_preferred'] for s in terms['series'])
    base = shares['value']
    return dict(
        preferred_shares=preferred,
        liquidation_preference_total=liquidation,
        as_converted_max_rate=dict(claim=0.0, shares_added=max_added,
                                   value_per_share=equity_before_preferred / (base + max_added)),
        as_converted_min_rate=dict(claim=0.0, shares_added=min_added,
                                   value_per_share=equity_before_preferred / (base + min_added)),
        liquidation_preference_claim=dict(claim=liquidation, shares_added=0.0,
                                          value_per_share=(equity_before_preferred - liquidation) / base),
    )


def build_receipt(ticker, facts, enterprise, valuation_date, preferred_terms=None):
    comp = build_components(facts, valuation_date)
    debt, notes = debt_and_lease_claims(comp)
    nonop = nonoperating_assets(comp)
    shares = share_count(facts, valuation_date)
    if shares is None:
        raise ValueError(f'{ticker}: no point-in-time share count; per-share value not computed.')
    result = equity_per_share(enterprise['enterprise_value'], comp, shares, debt, nonop)
    receipt = dict(ticker=ticker, valuation_date=valuation_date.isoformat(),
                   source='SEC public companyfacts', attestation='NOT_ZION_ATTESTED',
                   enterprise_artifact_valuation_date=enterprise['valuation_date'],
                   operating_assumptions=enterprise['analyst_assumptions'],
                   components=comp, shares=shares, notes=notes, result=result)
    if preferred_terms is not None:
        if 'PreferredStockValue' in comp:
            raise ValueError(f'{ticker}: PreferredStockValue is reported; reconcile before adding terms.')
        reported = pit_instant(facts, 'PreferredStockSharesOutstanding', valuation_date, unit='shares')
        scenarios = preferred_terms_scenarios(preferred_terms, result['common_equity_value'], shares)
        if reported and abs(reported['value'] - scenarios['preferred_shares']) > PREFERRED_SHARE_ROUNDING_TOLERANCE:
            raise ValueError(f"{ticker}: reported preferred shares {reported['value']} conflict with terms {scenarios['preferred_shares']}")
        receipt['preferred'] = dict(terms=preferred_terms, reported_shares_outstanding=reported,
                                    scenarios=scenarios, primary='as_converted_max_rate',
                                    legacy_assumed_absent_value_per_share=result['value_per_share'])
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--ticker', required=True)
    parser.add_argument('--companyfacts', required=True)
    parser.add_argument('--enterprise-artifact', required=True)
    parser.add_argument('--valuation-date', required=True)
    parser.add_argument('--preferred-terms', help='JSON file of offering terms for convertible preferred')
    parser.add_argument('--output')
    args = parser.parse_args()
    with open(args.companyfacts) as fh:
        facts = json.load(fh)['facts']
    with open(args.enterprise_artifact) as fh:
        enterprise = json.load(fh)['result']
    terms = None
    if args.preferred_terms:
        with open(args.preferred_terms) as fh:
            terms = json.load(fh)
    receipt = build_receipt(args.ticker, facts, enterprise, date.fromisoformat(args.valuation_date),
                            preferred_terms=terms)
    text = json.dumps(receipt, indent=1, sort_keys=True)
    if args.output:
        with open(args.output, 'w') as fh:
            fh.write(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
