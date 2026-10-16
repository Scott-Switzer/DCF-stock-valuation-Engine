"""One frozen scenario through the real loader, editor, brief, save and export."""
from copy import deepcopy
from dataclasses import asdict
import json

import pytest

from app import app, default_form, evaluate, form_payload
from auto_loading import load_method
from brief import build_brief
from compare import coerce_dcf_assumptions, recalculated_wacc
from dcf_loader import demo_document
from tax_policy import document_tax_policy
from test_xlsx_export import cells


def frozen_scenario():
    doc = demo_document()
    # Non-round ratios expose precision loss on an otherwise untouched form.
    doc['historical'][0]['ebit'] += 1.23456789
    for row, tax in zip(doc['historical'], [.22, -.153, .358]):
        row['tax_rate'] = tax
    doc['source']['capital_costs'] = {
        'market_equity_value': 5000., 'debt': 1000.,
        'cost_of_equity': .10, 'cost_of_debt': .06, 'wacc': .08975333333333334,
    }
    doc['source']['tax_policy'] = document_tax_policy(doc['historical'], scenario={
        'rates': [.231, .24, .25, .26, .27],
        'evidence': {'filing': 'Frozen synthetic regression', 'period_end': doc['historical'][-1]['period_end']},
    })
    return doc


def test_selected_policy_populates_all_editor_years_without_changing_history():
    doc = frozen_scenario()
    original = deepcopy(doc)
    form = default_form(doc)
    assert [form[f'tax_rate_{i}'] / 100 for i in range(5)] == pytest.approx([.231, .24, .25, .26, .27])
    assert form['wacc'] == recalculated_wacc(doc['source']['capital_costs'], .231) * 100
    assert doc == original


def test_all_scenario_paths_preserve_effective_assumptions_and_results(tmp_path, monkeypatch):
    monkeypatch.setenv('DCF_STATE_PATH', str(tmp_path / 'research.sqlite3'))
    monkeypatch.setitem(app.config, 'STATE_PATH', str(tmp_path / 'state.sqlite3'))
    doc = frozen_scenario()
    bundle = load_method('dcf', 'DEMO', snapshot=doc)
    costs = doc['source']['capital_costs']
    canonical, _ = coerce_dcf_assumptions(doc, None, costs['wacc'], costs=costs)
    expected = evaluate(doc, canonical)
    assert bundle['preview']['wacc'] == expected['wacc']
    assert bundle['preview']['intrinsic_value'] == expected['intrinsic_value']
    edited_doc, edited = form_payload(bundle['form'])
    for key in ('tax_rates', 'ebit_margins', 'da_margins', 'capex_margins', 'nwc_margins', 'wacc_override'):
        assert asdict(edited)[key] == asdict(canonical)[key], key
    assert edited_doc['historical'] == doc['historical']
    client = app.test_client()
    request = {'financials': edited_doc, 'assumptions': asdict(edited)}
    preview = client.post('/api/preview/dcf', json=request)
    assert preview.status_code == 200
    brief = build_brief(edited_doc, asdict(edited))
    saved = client.post('/api/research', json={**request, 'method': 'dcf', 'title': 'Frozen scenario'})
    assert saved.status_code == 201, saved.get_json()
    identity = saved.get_json()['id']
    restored = client.get(f'/api/research/{identity}').get_json()['snapshot']
    exported = client.post('/export/json', json=request).get_json()['result']
    for result in (bundle['preview'], preview.get_json(), restored['result'], exported):
        for key in ('wacc', 'intrinsic_value', 'enterprise_value', 'equity_value', 'terminal_value', 'projections'):
            assert result[key] == expected[key], key
    assert brief['dcf']['intrinsic_value'] == expected['intrinsic_value']
    assert brief['assumptions']['forecast_tax_rates'] == canonical.tax_rates
    assert restored['assumptions'] == asdict(edited)
    workbook = client.get(f'/research/{identity}/export/xlsx')
    assert workbook.status_code == 200
    sheets = cells(workbook.data)
    inputs = {address: value for address, formula, value in sheets['xl/worksheets/sheet2.xml']}
    assert float(inputs['B2']) == canonical.wacc_override
    assert [float(inputs[f'B{i}']) for i in range(37, 42)] == canonical.tax_rates
    # Export JSON is a reproducible calculated result, not a caller-supplied cache.
    assert json.loads(client.post('/export/json', json=request).data)['result']['intrinsic_value'] == expected['intrinsic_value']

@pytest.mark.parametrize('mode', ['recalculated', 'fixed'])
def test_edited_json_tax_shield_is_consistent_in_preview_brief_save_export(mode, tmp_path, monkeypatch):
    monkeypatch.setenv('DCF_STATE_PATH', str(tmp_path / 'research.sqlite3'))
    monkeypatch.setitem(app.config, 'STATE_PATH', str(tmp_path / 'state.sqlite3'))
    doc = frozen_scenario()
    costs = doc['source']['capital_costs']
    a, _ = coerce_dcf_assumptions(doc, None, costs['wacc'], costs=costs)
    raw = asdict(a)
    raw.update(tax_rates=[.30] * 5, interest_tax_shield_rate=.19, wacc_mode=mode)
    expected_wacc = recalculated_wacc(costs, .19) if mode == 'recalculated' else a.wacc_override
    c = app.test_client()
    payload = {'financials': doc, 'assumptions': raw}
    preview = c.post('/api/preview/dcf', json=payload).get_json()
    brief = c.post('/api/brief', json=payload).get_json()
    saved = c.post('/api/research', json={**payload, 'method': 'dcf', 'title': 'Tax edit'}).get_json()
    exported = c.post('/export/json', json=payload).get_json()
    assert preview['wacc'] == expected_wacc
    assert brief['dcf']['wacc'] == expected_wacc
    for result in (saved['snapshot']['result'], exported['result']):
        assert result['wacc'] == expected_wacc
        assert result['projections'] == preview['projections']
        assert result['intrinsic_value'] == preview['intrinsic_value']
    assert brief['dcf']['intrinsic_value'] == preview['intrinsic_value']


def test_yahoo_fallback_explicit_scenario_matches_editor_preview_and_brief(monkeypatch):
    import auto_loading
    import ppe_provider
    from test_yahoo_provider import MockHTTP, TODAY
    from yahoo_provider import load_yahoo

    http = MockHTTP()
    doc = load_yahoo('TEST', TODAY, http)
    original = deepcopy(doc)
    monkeypatch.setattr(ppe_provider, 'load_packet', lambda *a, **k: None)
    monkeypatch.setattr(auto_loading, 'load_yahoo', lambda *a, **k: deepcopy(doc))
    monkeypatch.setattr(auto_loading, 'company_classification', lambda *a: None)
    scenario = {'rates': [.231, .24, .25, .26, .27], 'evidence': {'filing': 'fixture', 'period_end': '2024-12-31'}}
    bundle = load_method('dcf', 'TEST', TODAY, http=http, tax_scenario=scenario)
    assert bundle['financials']['source']['statement_source'] == 'Yahoo'
    restored_doc, assumptions = form_payload(bundle['form'])
    edited = evaluate(restored_doc, assumptions)
    assert assumptions.tax_rates == scenario['rates']
    assert edited['intrinsic_value'] == bundle['preview']['intrinsic_value'] == bundle['brief']['dcf']['intrinsic_value']
    assert edited['wacc'] == bundle['preview']['wacc'] == bundle['brief']['dcf']['wacc']
    assert restored_doc['historical'] == original['historical']
