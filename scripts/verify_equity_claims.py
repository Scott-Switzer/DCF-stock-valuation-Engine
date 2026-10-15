"""Produce a source-backed equity claims reconciliation and per-share valuation.

This runs the real Zion claims extraction over downloaded SEC Company Facts, wraps the
result exactly as the Zion route does, verifies it with the DCF consumer, and values it
with the existing enterprise valuation for each company. No network access, no writes
outside the named output directory, and no provider calls.

    python3 scripts/verify_equity_claims.py --output-dir artifacts/zero-subscription-integration

The Zion checkout must be importable: set ZION_CLAIMS_SRC or rely on the sibling path.
"""
import argparse
from datetime import date
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from equity_claims_provider import (  # noqa: E402
    ProviderError,
    load_equity_claims,
    term_consistency,
    unresolved_claims,
    value_per_share,
    verify_claims,
)

# CIK 0001045810 is NVIDIA CORP; Microsoft is CIK 0000789019. Each document's own cik is
# checked against this table below, so a mislabelled facts file fails instead of being valued.
COMPANIES = (
    ('AAPL', '0000320193'),
    ('MSFT', '0000789019'),
    ('GOOGL', '0001652044'),
)
DEFAULT_ZION_SRC = '/Users/scottthomasswitzer/Documents/zion-valuation-service/deploy/cloudflare-query/src'


def zion(name):
    source = os.environ.get('ZION_CLAIMS_SRC', DEFAULT_ZION_SRC)
    if not Path(source).is_dir():
        raise SystemExit('set ZION_CLAIMS_SRC to the Zion deploy/cloudflare-query/src directory')
    if source not in sys.path:
        sys.path.insert(0, source)
    import importlib

    return importlib.import_module(name)


def contract(cik, document, valuation_date, terms=None, release='a' * 64):
    """Wrap the upstream claims the way the Zion route does, including its provenance pins."""
    facts = document['facts']
    claims = zion('equity_claims').build_claims(facts, valuation_date, cik=cik, preferred_terms=terms)
    return dict(
        claims,
        release_id=release,
        registry_sha256='c' * 64,
        manifest_sha256='d' * 64,
        member_sha256=hashlib.sha256(json.dumps(facts, sort_keys=True).encode()).hexdigest(),
        company_label=document.get('entityName'),
        audit={'authenticated_via': 'SERVICE_CREDENTIAL', 'caller': 'dcf-valuation-engine'},
        provenance={
            'engine': 'NATIVE_IMMUTABLE_SEC_EQUITY_CLAIMS',
            'source': 'SEC_COMPANY_FACTS_PINNED_ARCHIVE_MEMBER',
            'source_lineage': {'rights': 'PUBLIC_SEC_ONLY', 'licensed_sources_used': False},
        },
    )


class FixtureTransport:
    """Stands in for the service-binding transport: serves one pinned page and nothing else."""

    def __init__(self, page):
        self.page = page
        self.calls = []

    def get(self, url, *, headers, params):
        self.calls.append(dict(url=url, headers=headers, params=params))
        if len(self.calls) > 1:
            raise AssertionError('the consumer must fetch the claims contract exactly once')
        return self.page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--facts-dir', type=Path,
                        default=Path('artifacts/zero-subscription-integration/companyfacts'))
    parser.add_argument('--artifacts-dir', type=Path,
                        default=Path('artifacts/zero-subscription-integration'))
    parser.add_argument('--terms', type=Path, default=Path('fixtures/alphabet-mandatory-convertible-terms.json'))
    parser.add_argument('--as-of', default='2026-10-14')
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    terms_path = args.terms
    if not terms_path.is_file():
        raise SystemExit('offering terms file not found: ' + str(terms_path))
    terms = json.loads(terms_path.read_bytes())
    valuation_date = date.fromisoformat(args.as_of)
    receipts, failures = {}, []
    for ticker, cik in COMPANIES:
        facts_path = next(
            (candidate for candidate in (args.facts_dir / (cik + '.json'),
                                         args.facts_dir / (ticker + '-companyfacts.json'))
             if candidate.is_file()),
            None,
        )
        if facts_path is None:
            failures.append(dict(ticker=ticker, reason='MISSING_COMPANY_FACTS',
                                 path=str(args.facts_dir)))
        document = json.loads(facts_path.read_bytes())
        if str(document.get('cik')).zfill(10) != cik:
            failures.append(dict(ticker=ticker, reason='COMPANY_IDENTITY_MISMATCH',
                                 expected_cik=cik, document_cik=document.get('cik'),
                                 entity_name=document.get('entityName')))
            continue
        page = contract(cik, document, valuation_date, terms=terms if ticker == 'GOOGL' else None)
        transport = FixtureTransport(page)
        try:
            claims = load_equity_claims(ticker, args.as_of, transport, cik=cik,
                                        base='https://zion.invalid',
                                        service_token='local-service-credential',
                                        caller='dcf-valuation-engine',
                                        expected_release_id=page['release_id'])
        except ProviderError as error:
            failures.append(dict(ticker=ticker, reason='CLAIMS_REJECTED', detail=str(error)))
            continue
        enterprise_path = next(
            (candidate for candidate in (args.artifacts_dir / (ticker + '-enterprise-verification.json'),
                                         Path('../artifacts/zero-subscription-integration')
                                         / (ticker + '-enterprise-verification.json'))
             if candidate.is_file()),
            None,
        )
        if enterprise_path is None:
            failures.append(dict(ticker=ticker, reason='MISSING_ENTERPRISE_ARTIFACT'))
            continue
        enterprise = json.loads(enterprise_path.read_bytes())['result']
        bridge = value_per_share(enterprise['enterprise_value'], claims,
                                 preferred_terms=terms if ticker == 'GOOGL' else None,
                                 scenario='AS_CONVERTED_MAX_RATE')
        scenario_terms = claims['claims']['preferred_equity'].get('dilution_terms')
        receipts[ticker] = dict(
            ticker=ticker, cik=cik, entity_name=document.get('entityName'),
            valuation_date=args.as_of,
            enterprise_value=enterprise['enterprise_value'],
            enterprise_artifact=enterprise_path.name,
            claims=_claim_summary(claims),
            aggregate_claims=claims['aggregate_claims'],
            preferred_treatment=_preferred_treatment(claims),
            noncontrolling_treatment=_noncontrolling_treatment(claims),
            valuation=dict(
                primary_scenario=bridge['primary_scenario'],
                equity_value=bridge['primary']['equity_value'],
                value_per_share=bridge['primary']['value_per_share'],
                shares_outstanding=bridge['shares_outstanding'],
                shares_basis=bridge['shares_basis'],
                bridge_inputs=bridge['bridge_inputs'],
                scenarios=bridge['scenarios'],
            ),
            unresolved=unresolved_claims(claims),
            term_consistency=(term_consistency(claims, terms)['status'] if scenario_terms else 'NOT_COMPARABLE'),
            source=claims['source'],
        )
        _write(args.output_dir / (ticker + '-equity-claims.json'),
               dict(summary=receipts[ticker]['valuation'], result=receipts[ticker]))
    summary = dict(schema_version='zion-equity-claims-reconciliation-v1', as_of=args.as_of,
                   companies=receipts, failures=failures)
    _write(args.output_dir / 'equity-claims-reconciliation.json', summary)
    print(json.dumps(_printable(receipts, failures), indent=1, sort_keys=True))


def _claim_summary(claims):
    return {
        name: dict(evidence_state=claim['evidence_state'], value_decimal=claim['value_decimal'],
                   unit=claim['unit'], period_end=claim.get('period_end'),
                   available_at=claim.get('available_at'), sources=len(claim['sources']),
                   evidence_digest=claim['evidence_digest'])
        for name, claim in sorted(claims['claims'].items())
    }


def _preferred_treatment(claims):
    preferred = claims['claims']['preferred_equity']
    return {
        'evidence_state': preferred['evidence_state'],
        'carrying_value_decimal': preferred.get('carrying_value_decimal'),
        'carrying_concept': preferred.get('carrying_concept'),
        'shares_outstanding_decimal': preferred.get('shares_outstanding_decimal'),
        'liquidation_preference_per_share_decimal': preferred.get('liquidation_preference_per_share_decimal'),
        'dividend_rate_decimal': preferred.get('dividend_rate_decimal'),
        'dilution_terms_state': (preferred.get('dilution_terms') or {}).get('evidence_state'),
        'dilution_terms_basis': (preferred.get('dilution_terms') or {}).get('basis'),
        'conflicts': preferred.get('conflicts'),
    }


def _noncontrolling_treatment(claims):
    noncontrolling = claims['claims']['noncontrolling_interests']
    return {
        'evidence_state': noncontrolling['evidence_state'],
        'value_decimal': noncontrolling['value_decimal'],
        'classification': noncontrolling.get('classification'),
        'treatment': noncontrolling.get('treatment'),
        'deduction_permitted': noncontrolling.get('deduction_permitted'),
        'redeemable_subset': noncontrolling.get('redeemable_subset'),
        'conflicts': noncontrolling.get('conflicts'),
    }


def _write(path, payload):
    body = json.dumps(payload, indent=1, sort_keys=True, allow_nan=False)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write(body + '\n')


def _printable(receipts, failures):
    rows = {}
    for ticker, receipt in sorted(receipts.items()):
        valuation = receipt['valuation']
        rows[ticker] = dict(
            enterprise_value=receipt['enterprise_value'],
            primary_scenario=valuation['primary_scenario'],
            equity_value=valuation['equity_value'],
            value_per_share=valuation['value_per_share'],
            shares_outstanding=valuation['shares_outstanding'],
            noncontrolling=receipt['noncontrolling_treatment']['value_decimal'],
            noncontrolling_state=receipt['noncontrolling_treatment']['evidence_state'],
            preferred_state=receipt['preferred_treatment']['evidence_state'],
            unresolved_blocking=[entry['claim'] for entry in receipt['unresolved']['blocking']],
        )
    return dict(companies=rows, failures=failures)


if __name__ == '__main__':
    main()
