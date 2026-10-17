"""Operating-only scenario using the existing DCF discount core.

Reinvestment is explicitly modeled as delta revenue / sales-to-capital. It is
not reported historical capex, D&A or working capital. Missing equity claims
remain missing and never enter this enterprise-only calculation as zeros.
"""
from copy import deepcopy
from datetime import date, datetime, timezone
from dcf_code import DCFAssumptions, discount_fcff, number
from dcf_loader import ProviderError
from zion_history_provider import verify_evidence


BRIDGE_MANDATORY=('short_term_debt','long_term_debt','cash','preferred_equity','minority_interest','other_nonoperating_assets')


def equity_bridge(bridge, enterprise_value, shares_outstanding=None, shares_basis=None):
    """Enterprise-to-equity bridge. Every claim must be explicit; absence is never zero.

    Weighted-average diluted shares are rejected: they are not a point-in-time share count.
    """
    missing=[k for k in BRIDGE_MANDATORY if not isinstance(bridge,dict) or bridge.get(k) is None]
    if shares_outstanding is None:
        missing.append('shares_outstanding')
    elif shares_basis!='COMMON_SHARES_OUTSTANDING':
        raise ValueError('Shares must be a point-in-time common share count, not weighted-average diluted shares.')
    if missing:
        return dict(status='UNAVAILABLE',missing=missing,equity_value=None,value_per_share=None)
    claims=sum(number(bridge[k],k) for k in ('short_term_debt','long_term_debt','preferred_equity','minority_interest'))
    equity=number(enterprise_value,'Enterprise value')+number(bridge['cash'],'Cash')+number(bridge['other_nonoperating_assets'],'Other nonoperating assets')-claims
    if shares_outstanding<=0:
        raise ValueError('Shares outstanding must be positive.')
    return dict(status='AVAILABLE',missing=[],equity_value=equity,value_per_share=equity/shares_outstanding)


def value_enterprise(doc, benchmarks, growth_rates, terminal_growth, terminal_roic, *, valuation_date, suitable, evidence_secret=None):
    if suitable is not True:
        raise ValueError('Confirm operating-company suitability for FCFF.')
    value_date=date.fromisoformat(valuation_date)
    today=datetime.now(timezone.utc).date()
    if value_date>today:
        raise ValueError('Valuation date cannot be in the future.')
    if not isinstance(doc, dict):
        raise ValueError('Verified native Zion input bundle required.')
    source=doc.get('source',{})
    if source.get('adapter_version')!='zion-native-history-v1':
        raise ValueError('Verified native Zion input bundle required.')
    # Reconstruct from server-attested frozen evidence rather than trusting caller-supplied fields.
    try:
        verified=verify_evidence(doc, evidence_secret)
    except ProviderError as exc:
        raise ValueError(str(exc)) from exc
    if date.fromisoformat(doc['valuation_date'])>value_date:
        raise ValueError('Financial cutoff exceeds valuation date.')
    verified['source']['evidence_attestation']=deepcopy(source.get('evidence_attestation'))
    # The model names the three reference assumptions it needs. The served DDFI corpus names
    # the sales/capital ratio `sales_to_invested_capital`, while the earlier file-based DDFI
    # releases named the same measure from the same source bytes `sales_capital`; both names
    # describe the one concept, so both are accepted and the served name is what the result
    # records. Any other measure name is still refused.
    expected={'wacc':(('wacc',),'fraction'),'tax_rate':(('tax_rate',),'fraction'),
              'sales_capital':(('sales_capital','sales_to_invested_capital'),'ratio')}
    values={}
    for target,(measures,unit) in expected.items():
        row=benchmarks.get(target,{})
        if (row.get('measure') not in measures or row.get('unit')!=unit or not row.get('release_id')
                or row.get('classification')!='BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT'):
            raise ValueError('Explicit compatible benchmark required: '+target)
        if row.get('published_at'):
            if date.fromisoformat(row['published_at'])>value_date:
                raise ValueError('Benchmark published after valuation date.')
        elif row.get('selection_mode')!='CURRENT_EXPLICIT_SELECTION' or value_date!=today:
            raise ValueError('Unknown benchmark vintage cannot be backdated.')
        values[target]=number(row['value_decimal'],target)
    wacc=number(values['wacc'],'WACC',.001,.5)
    tax=number(values['tax_rate'],'Modeled tax rate',0,1)
    sales_capital=number(values['sales_capital'],'Sales/capital',.000001)
    assumptions=DCFAssumptions(growth_rates,terminal_growth,wacc_override=wacc,
                               terminal_mode='normalized',terminal_roic=terminal_roic)
    assumptions.validate()
    actual=verified['historical'][-1]
    revenue=number(actual['revenue'],'Reported revenue',.000001)
    ebit=number(actual['ebit'],'Reported operating income')
    margin=ebit/revenue
    rows=[]
    for year,growth in enumerate(assumptions.revenue_growth_rates,1):
        previous=revenue;revenue*=1+growth
        nopat=revenue*margin*(1-tax)
        reinvestment=(revenue-previous)/sales_capital
        rows.append(dict(Year=year,Revenue=revenue,EBIT=revenue*margin,NOPAT=nopat,
                         ModeledReinvestment=reinvestment,UFCF=nopat-reinvestment))
    result=discount_fcff(rows,wacc,terminal_growth,terminal_mode='normalized',terminal_roic=terminal_roic)
    result.update(schema_version='zion-enterprise-dcf-v1',model_version='cuig-discount-core-v1-sales-capital-scenario',
        valuation_date=valuation_date,financial_cutoff=doc['valuation_date'],projections=rows,
        equity_value=None,intrinsic_value=None,target_price_12m=None,
        status='ENTERPRISE_SCENARIO_ONLY',source=deepcopy(verified['source']),
        benchmark_assumptions=deepcopy(benchmarks),
        analyst_assumptions=dict(revenue_growth_rates=growth_rates,terminal_growth=terminal_growth,
                                 terminal_roic=terminal_roic,operating_margin_policy='HOLD_LATEST_REPORTED_MARGIN',
                                 reinvestment_policy='DELTA_REVENUE_OVER_INDUSTRY_SALES_CAPITAL',
                                 company_suitability_confirmed=True),
        warnings=['An assumption-driven operating valuation, not a verified fair-price recommendation.',
                  'Historical facts retain their actual period and availability; no freshness substitution.',
                  'Debt, other claims and share inputs remain incomplete. Equity and per-share values are unavailable.',
                  'Industry tax, WACC and capital efficiency are selected assumptions, not company observations.'])
    result['equity_bridge']=equity_bridge(verified.get('bridge'),result['enterprise_value'])
    return result
