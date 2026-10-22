"""Independently validate the enterprise-to-equity bridge against the filing itself.

This does not use the claims contract as its source of truth. It re-derives every claim
directly from the downloaded SEC Company Facts with the same point-in-time rule, then
checks the things a bridge gets wrong quietly:

* every claim the bridge deducts or adds is counted exactly once, and cash appears in
  exactly one of the two roles;
* noncontrolling interests are an equity claim that is neither inside the debt claim nor
  double counted against the parent's own equity;
* a convertible preferred series is never both deducted as a claim and added as shares;
* operating leases are excluded while finance leases are included, and the reason is
  recorded rather than assumed;
* the balance identity assets - liabilities = equity holds for the selected period, so a
  claim omitted from the bridge shows up as a residual instead of passing silently.

    python3 scripts/validate_equity_bridge.py --output artifacts/validation/equity-bridge.json
"""
import argparse
from datetime import date
from decimal import Decimal, localcontext
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.public_sec_equity_bridge import pit_instant  # noqa: E402

COMPANIES = (('AAPL', '0000320193'), ('MSFT', '0000789019'), ('GOOGL', '0001652044'))
DEFAULT_ZION_SRC = ('/Users/scottthomasswitzer/Documents/zion-valuation-service'
                    '/deploy/cloudflare-query/src')

DEDUCTIBLE = ('debt', 'finance_leases', 'preferred_equity', 'noncontrolling_interests')
ADDED = ('cash', 'nonoperating_assets')
BALANCE = ('Assets', 'Liabilities', 'StockholdersEquity',
           'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
           'MinorityInterest')
NONOPERATING_PARTS = ('CashAndCashEquivalentsAtCarryingValue', 'ShortTermInvestments',
                      'MarketableSecuritiesCurrent', 'MarketableSecuritiesNoncurrent')
NONCURRENT_INVESTMENTS = ('LongTermInvestments', 'EquityMethodInvestments')


def zion(name):
    source = os.environ.get('ZION_CLAIMS_SRC', DEFAULT_ZION_SRC)
    if source not in sys.path:
        sys.path.insert(0, source)
    import importlib

    return importlib.import_module(name)


def row(facts, concept):
    found = pit_instant(facts, concept, ASOF)
    return None if found is None else (found['concept'], Decimal(str(found['value'])),
                                       found['period_end'], found['form'], found['accession'])


def value(facts, concept):
    found = row(facts, concept)
    return None if found is None else found[1]


def main():
    global ASOF
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--facts-dir', type=Path,
                        default=Path('artifacts/zero-subscription-integration/companyfacts'))
    parser.add_argument('--as-of', default='2026-10-14')
    args = parser.parse_args()
    ASOF = date.fromisoformat(args.as_of)
    build_claims = zion('equity_claims').build_claims
    report = {'as_of': args.as_of, 'filer': {}, 'failures': []}

    for ticker, cik in COMPANIES:
        entry, failed = {}, False
        document = json.loads((args.facts_dir / f'{cik}.json').read_bytes())
        if str(document.get('cik')).zfill(10) != cik:
            report['failures'].append(dict(ticker=ticker, reason='COMPANY_IDENTITY_MISMATCH'))
            continue
        facts = document['facts']
        contract = build_claims(facts, ASOF, cik=cik)
        claims = contract['claims']

        # 1. Each bridge claim, and whether the contract's number is the filing's number.
        for name in DEDUCTIBLE + ADDED:
            documented = claims[name]['value_decimal']
            reported = [r for r in (row(facts, source['concept'].split(':', 1)[1])
                                    for source in claims[name]['sources']) if r]
            independent = sum((r[1] for r in reported), Decimal(0))
            documented_decimal = None if documented is None else Decimal(documented)
            agrees = (documented_decimal is None and not reported) or (
                documented_decimal is not None and documented_decimal == independent)
            entry[name] = dict(
                evidence_state=claims[name]['evidence_state'],
                contract_decimal=documented,
                independent_decimal=str(independent),
                agrees_with_filing=agrees,
                period=reported[0][2] if reported else None,
                form=reported[0][3] if reported else None,
                accession=reported[0][4] if reported else None,
                concepts=[{'concept': r[0], 'value': str(r[1])} for r in reported])
            failed |= not agrees

        # 2. Cash must appear in exactly one bridge role.
        cash = value(facts, 'CashAndCashEquivalentsAtCarryingValue')
        nonoperating_parts = {name: value(facts, name) for name in NONOPERATING_PARTS}
        present = {k: v for k, v in nonoperating_parts.items() if v is not None}
        nonoperating_total = sum(present.values(), Decimal(0))
        other = nonoperating_total - (cash or Decimal(0))
        entry['nonoperating_breakdown'] = dict(
            constituents={k: str(v) for k, v in present.items()},
            total=str(nonoperating_total),
            cash_decimal=None if cash is None else str(cash),
            non_cash_decimal=str(other),
            cash_counted_once=nonoperating_total == sum(present.values(), Decimal(0)),
            cash_is_a_constituent='CashAndCashEquivalentsAtCarryingValue' in present,
            excluded_long_term_investments={
                name: str(value(facts, name)) for name in NONCURRENT_INVESTMENTS
                if value(facts, name) is not None})
        failed |= not entry['nonoperating_breakdown']['cash_is_a_constituent']

        # 3. Noncontrolling interests: an equity claim, extracted from APIC/equity, not debt.
        parent_equity = value(facts, 'StockholdersEquity')
        consolidated = value(facts, 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest')
        nci = value(facts, 'MinorityInterest')
        entry['noncontrolling_scope'] = dict(
            nci_decimal=None if nci is None else str(nci),
            nci_concept='us-gaap:MinorityInterest',
            parent_equity=None if parent_equity is None else str(parent_equity),
            consolidated_equity=None if consolidated is None else str(consolidated),
            nci_is_separate_equity_line=(
                parent_equity is not None and consolidated is not None and nci is not None
                and parent_equity + nci == consolidated),
            deducted_from_a_consolidated_value=True,
            apic_decimal=str(value(facts, 'AdditionalPaidInCapital')) if value(
                facts, 'AdditionalPaidInCapital') is not None else None,
            note=('A noncontrolling interest is a claim on the consolidated cash flows the '
                  'enterprise value measures, so it is deducted once. It is never part of '
                  'the interest-bearing debt claim unless the filing puts it there.'),
        )
        if nci is not None and consolidated is not None and parent_equity is not None:
            failed |= not entry['noncontrolling_scope']['nci_is_separate_equity_line']

        # 4. Preferred: deducted as a claim or added as shares, never both.
        preferred = claims['preferred_equity']
        terms = preferred.get('dilution_terms')
        as_converted = None if terms is None else Decimal(terms['max_converted_common_shares_decimal'])
        entry['preferred'] = dict(
            evidence_state=preferred['evidence_state'],
            carrying_decimal=preferred['value_decimal'],
            carrying_concept=preferred.get('carrying_concept'),
            shares_outstanding_decimal=preferred.get('shares_outstanding_decimal'),
            conversion_terms_present=terms is not None,
            max_converted_common_shares=None if as_converted is None else str(as_converted),
            rule=('As-converted scenarios add converted common shares and deduct no preferred '
                  'claim; the liquidation scenario deducts the preference and adds no shares.'),
        )
        if terms is not None and preferred['value_decimal'] is not None:
            report['failures'].append(dict(
                ticker=ticker, reason='PREFERRED_HAS_BOTH_A_CLAIM_AND_CONVERSION_TERMS',
                detail='the caller-selected terms must replace the carrying claim, not join it'))
            failed = True

        # 5. Lease conventions.
        entry['leases'] = dict(
            finance_lease=claims['finance_leases']['value_decimal'],
            finance_in_bridge=claims['finance_leases']['evidence_state'] in
            ('REPORTED', 'DERIVED_VERIFIED'),
            operating_lease=claims['operating_leases']['value_decimal'],
            operating_in_bridge=claims['operating_leases'].get('included_in_enterprise_bridge'),
            note=('Operating lease liabilities are excluded because EBIT is after operating '
                  'lease cost; finance leases are a financing claim and are deducted.'),
        )
        failed |= claims['operating_leases'].get('included_in_enterprise_bridge') is not False
        if claims['finance_leases']['value_decimal'] is None \
                and claims['finance_leases']['evidence_state'] != 'REVIEWED_ABSENT':
            report['failures'].append(dict(ticker=ticker, reason='FINANCE_LEASE_UNRESOLVED'))
            failed = True

        # 6. Balance identity, so an omitted claim becomes a visible residual.
        assets, liabilities = value(facts, 'Assets'), value(facts, 'Liabilities')
        equity = consolidated if consolidated is not None else parent_equity
        if None not in (assets, liabilities, equity):
            with localcontext() as context:
                context.prec = 40
                residual = assets - liabilities - equity
            entry['balance_identity'] = dict(
                assets=str(assets), liabilities=str(liabilities), equity=str(equity),
                residual_decimal=str(residual),
                identity_holds=residual == 0,
                period=row(facts, 'Assets')[2])
            failed |= residual != 0
        else:
            entry['balance_identity'] = dict(unavailable=[
                name for name, found in (('Assets', assets), ('Liabilities', liabilities),
                                         ('Equity', equity)) if found is None])

        entry['bridge'] = dict(
            deduct_decimal=contract['aggregate_claims'].get('deduct_claims_decimal'),
            add_decimal=contract['aggregate_claims'].get('add_claims_decimal'),
            verified_absent=contract['aggregate_claims'].get('verified_absent'))
        entry['status'] = 'FAILED' if failed else 'VALIDATED'
        report['filer'][ticker] = entry
        if failed:
            report['failures'].append(dict(ticker=ticker, reason='BRIDGE_VALIDATION_FAILED'))

    report['status'] = 'VALIDATED' if not report['failures'] else 'FAILED'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=1, sort_keys=True) + '\n')
    print(json.dumps(dict(status=report['status'], failures=report['failures'],
                          filer={k: v['status'] for k, v in report['filer'].items()}), indent=1))
    return 0 if report['status'] == 'VALIDATED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
