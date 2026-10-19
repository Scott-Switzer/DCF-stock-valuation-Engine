from copy import deepcopy
import pytest
from scripts.verify_claims_cohort import reconcile


def outcome():
    return dict(enterprise_value=1000,bridge=dict(cash=100,other_nonoperating_assets=20,
        short_term_debt=30,long_term_debt=60,preferred_equity=10,minority_interest=20),
        shares_outstanding=100,primary_scenario='NO_PREFERRED_OUTSTANDING',
        scenarios={'NO_PREFERRED_OUTSTANDING':dict(shares_added=0)},
        primary=dict(status='AVAILABLE',value_per_share=10),unresolved=dict(blocking=[]))


def test_independent_bridge_accounts_for_every_claim_and_conversion_share():
    row=outcome()
    assert reconcile(row)['value_per_share_decimal']=='10'
    row['scenarios']['NO_PREFERRED_OUTSTANDING']['shares_added']=25
    row['primary']['value_per_share']=8
    assert reconcile(row)['value_per_share_decimal']=='8'
    row['primary']['value_per_share']=10
    with pytest.raises(ValueError,match='reconciliation'):
        reconcile(row)


def test_unresolved_claims_cannot_produce_verified_receipt():
    row=deepcopy(outcome())
    row['unresolved']['blocking']=[{'claim':'cash'}]
    assert reconcile(row) is None
    row=outcome()
    row['primary']['status']='UNAVAILABLE'
    assert reconcile(row) is None
