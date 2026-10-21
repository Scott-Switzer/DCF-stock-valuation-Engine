"""Source-qualified recent capital claims; reported values only, no missing-to-zero fills."""
from datetime import date
import math

FORMS = {'10-K', '10-K/A', '10-Q', '10-Q/A'}
TAGS = {
    'assets': ['Assets'], 'current_assets': ['AssetsCurrent'],
    'current_liabilities': ['LiabilitiesCurrent'],
    'cash': ['CashAndCashEquivalentsAtCarryingValue'],
    'short_term_debt': ['DebtCurrent'],
    'current_maturities': ['LongTermDebtCurrent', 'LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths'],
    'short_term_borrowings': ['ShortTermBorrowings', 'CommercialPaper'],
    'long_term_debt': ['LongTermDebtNoncurrent'],
    'debt_including_current': ['LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities'],
    'preferred_equity': ['PreferredStockValue'],
    'minority_interest': ['MinorityInterest'],
    'parent_equity': ['StockholdersEquity'], 'common_equity': ['CommonStockEquity'],
    'total_equity': ['StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],
    'diluted_shares': ['WeightedAverageNumberOfDilutedSharesOutstanding'],
}


def recent_claims(facts, cik, cutoff, source):
    if str(facts.get('cik', '')).zfill(10) != cik:
        raise ValueError('CLAIMS_CIK_MISMATCH')
    date.fromisoformat(cutoff)
    tags = facts.get('facts', {}).get('us-gaap', {})
    contexts = []
    for tag in ['Assets', 'StockholdersEquity', 'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest']:
        for r in tags.get(tag, {}).get('units', {}).get('USD', []):
            if (r.get('form') in FORMS and not r.get('start') and r.get('accn')
                    and r.get('end', '9999') <= cutoff and r.get('filed', '9999') <= cutoff):
                contexts.append(r)
    if not contexts and facts.get('facts', {}).get('ifrs-full'):
        return {'status': 'UNSUPPORTED_IFRS_ADAPTER', 'fields': {}, 'gaps': ['IFRS_ACCOUNTING_ADAPTER_REQUIRED']}
    if not contexts:
        return {'status': 'NO_BALANCE_CONTEXT', 'fields': {}, 'gaps': ['NO_BALANCE_CONTEXT']}
    end = max(r['end'] for r in contexts)
    filed = max(r['filed'] for r in contexts if r['end'] == end)
    accessions = {r['accn'] for r in contexts if r['end'] == end and r['filed'] == filed}
    if len(accessions) != 1:
        return {'status': 'AMBIGUOUS_LATEST_FILING', 'period_end': end, 'fields': {}, 'gaps': ['AMBIGUOUS_LATEST_FILING']}
    accession = accessions.pop()
    conflicts = []

    def pick(field):
        unit = 'shares' if field == 'diluted_shares' else 'USD'
        for tag in TAGS[field]:
            candidates = []
            for r in tags.get(tag, {}).get('units', {}).get(unit, []):
                if (r.get('end') != end or r.get('accn') != accession or r.get('filed') != filed
                        or r.get('form') not in FORMS):
                    continue
                if field == 'diluted_shares':
                    try:
                        days = (date.fromisoformat(end) - date.fromisoformat(r['start'])).days + 1
                    except (ValueError, KeyError, TypeError):
                        continue
                    if not (60 <= days <= 105 or 330 <= days <= 380):
                        continue
                elif r.get('start'):
                    continue
                value = r.get('val')
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    continue
                candidates.append(r)
            if not candidates:
                continue
            if field == 'diluted_shares':
                # Prefer the reported quarter; never add/subtract weighted-average shares.
                shortest = min((date.fromisoformat(end) - date.fromisoformat(r['start'])).days for r in candidates)
                candidates = [r for r in candidates if (date.fromisoformat(end) - date.fromisoformat(r['start'])).days == shortest]
            if len({r['val'] for r in candidates}) != 1:
                conflicts.append('CONFLICT_' + field.upper())
                return None
            r = candidates[0]
            return {'value': r['val'], 'unit': unit, 'period_end': end, 'available_at': filed,
                    'provenance': {**source, 'provider': 'SEC companyfacts', 'tag': tag,
                                   'accession': accession, 'filing_date': filed,
                                   'form': r['form'], 'period_start': r.get('start')}}
        return None

    fields = {field: pick(field) for field in TAGS}

    def derive(target, left, right, operation, formula):
        if fields[target] is not None or fields[left] is None or fields[right] is None:
            return
        value = operation(fields[left]['value'], fields[right]['value'])
        # Capital claims must be nonnegative. NCI/equity can be negative and remains reported.
        if target in {'short_term_debt', 'long_term_debt', 'preferred_equity'} and value < 0:
            conflicts.append('NEGATIVE_DERIVED_' + target.upper())
            return
        fields[target] = {'value': value, 'unit': 'USD', 'period_end': end, 'available_at': filed,
                          'provenance': {**source, 'provider': 'SEC same-filing derivation',
                                         'accession': accession, 'filing_date': filed, 'formula': formula,
                                         'components': [fields[left], fields[right]]}}

    derive('short_term_debt', 'current_maturities', 'short_term_borrowings', lambda a, b: a + b,
           'current maturities + short-term borrowings; explicit components required')
    derive('long_term_debt', 'debt_including_current', 'current_maturities', lambda a, b: a - b,
           'long-term debt including current minus current maturities')
    derive('preferred_equity', 'parent_equity', 'common_equity', lambda a, b: a - b,
           'parent stockholders equity minus common equity')
    derive('minority_interest', 'total_equity', 'parent_equity', lambda a, b: a - b,
           'total stockholders equity including NCI minus parent stockholders equity')
    required = ['cash', 'short_term_debt', 'long_term_debt', 'preferred_equity', 'minority_interest', 'diluted_shares']
    gaps = sorted(set(conflicts + ['MISSING_' + k.upper() for k in required if fields[k] is None]))
    additional_claims = []
    for namespace, concepts in facts.get('facts', {}).items():
        for tag, concept in concepts.items():
            if not tag.startswith(('Redeemable', 'MandatorilyRedeemable', 'TemporaryEquity', 'MezzanineEquity')):
                continue
            for r in concept.get('units', {}).get('USD', []):
                if (r.get('end') == end and not r.get('start') and r.get('accn') == accession
                        and r.get('filed') == filed and isinstance(r.get('val'), (int, float))
                        and not isinstance(r['val'], bool) and math.isfinite(r['val']) and r['val'] != 0):
                    additional_claims.append({'namespace': namespace, 'tag': tag, 'value': r['val'],
                                              'period_end': end, 'accession': accession})
    if additional_claims:
        gaps.append('ADDITIONAL_CAPITAL_CLAIMS_REQUIRE_CLASSIFICATION')
    for field in ['cash', 'short_term_debt', 'long_term_debt', 'preferred_equity']:
        if fields[field] is not None and fields[field]['value'] < 0:
            gaps.append('NEGATIVE_REPORTED_' + field.upper())
    if fields['diluted_shares'] is not None and fields['diluted_shares']['value'] <= 0:
        gaps.append('NONPOSITIVE_DILUTED_SHARES')
    return {'status': 'RECENT_CLAIM_FIELDS_PRESENT' if not gaps else 'RECENT_CLAIM_GAPS',
            'period_end': end, 'filed': filed, 'accession': accession, 'fields': fields, 'gaps': gaps,
            'additional_claims': additional_claims,
            'source_cutoff': cutoff, 'share_basis': 'REPORTED_WEIGHTED_AVERAGE_NOT_SPOT_OR_CLASS_SPECIFIC',
            'availability_policy': 'SEC_FILED_DATE_NOT_ACCEPTANCE_TIMESTAMP', 'valuation_ready': False}


def error_code(error):
    text = str(error)
    if text.startswith('No eligible annual PPE revenue'):
        return 'NO_ELIGIBLE_ANNUAL_REVENUE'
    if text.startswith(('Conflicting SEC', 'Conflicting PPE')):
        return 'CONFLICTING_REPORTED_FACTS'
    if text.startswith('PPE adjustment evidence build failed'):
        return 'ACCOUNTING_ADJUSTMENT_EVIDENCE_REJECTED'
    if text.startswith(('SEC issuer mismatch', 'PPE observation issuer mismatch')):
        return 'ISSUER_IDENTITY_MISMATCH'
    return 'PACKET_BUILD_REJECTED'
