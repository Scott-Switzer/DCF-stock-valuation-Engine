from sec_share_evidence import extract_shares


def filing(value='1234', *, segment='', unit='shares', instant='2026-09-01', cik='320193', extra=''):
    return f'''<xbrl xmlns="http://www.xbrl.org/2003/instance" xmlns:dei="http://xbrl.sec.gov/dei/2026"
      xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:us-gaap="http://fasb.org/us-gaap/2026">
      <context id="c"><entity><identifier scheme="http://www.sec.gov/CIK">{cik}</identifier>{segment}</entity>
      <period><instant>{instant}</instant></period></context>
      <unit id="u"><measure>{unit}</measure></unit>
      <dei:EntityCommonStockSharesOutstanding contextRef="c" unitRef="u">{value}</dei:EntityCommonStockSharesOutstanding>{extra}</xbrl>'''.encode()


def extract(raw, **kw):
    return extract_shares(raw, cik='0000320193', accession='0000320193-26-000001',
                          source_url='https://www.sec.gov/Archives/edgar/data/320193/000032019326000001/a.xml',
                          filed='2026-09-10', as_of=kw.pop('as_of', '2026-09-24'), **kw)


def test_reported_count_keeps_lineage():
    result = extract(filing())
    assert result['status'] == 'CANDIDATE_REQUIRES_REVIEW'
    assert result['facts'][0]['value_decimal'] == '1234'
    assert result['facts'][0]['period_end'] == '2026-09-01'
    assert result['source']['sha256'] and result['source']['accession']
    assert result['permitted_for_valuation'] is False


def test_class_dimensions_are_preserved_and_not_summed():
    segment = '<segment><xbrldi:explicitMember dimension="dei:StatementClassOfStockAxis">dei:ClassA</xbrldi:explicitMember></segment>'
    result = extract(filing(segment=segment))
    assert result['facts'][0]['dimensions'] == {'dei:StatementClassOfStockAxis': 'dei:ClassA'}
    assert result['aggregate_outstanding_shares'] is None


def test_conflicting_facts_are_not_selected():
    extra = '<dei:EntityCommonStockSharesOutstanding contextRef="c" unitRef="u">2222</dei:EntityCommonStockSharesOutstanding>'
    assert extract(filing(extra=extra))['status'] == 'CONFLICTING'


def test_future_filing_is_unavailable():
    assert extract(filing(), as_of='2026-09-09')['status'] == 'NOT_YET_AVAILABLE'


def test_stale_and_wrong_unit_and_wrong_issuer_are_explicit():
    for raw, reason in [(filing(instant='2020-01-01'), 'STALE_OBSERVATION'),
                        (filing(unit='USD'), 'UNSUPPORTED_UNIT'),
                        (filing(cik='789019'), 'ISSUER_MISMATCH'),
                        (filing(value='NaN'), 'INVALID_SHARE_VALUE')]:
        result = extract(raw)
        assert not result['facts'] and reason in result['rejected_reasons']


def test_weighted_average_is_not_outstanding():
    raw = filing().replace(b'EntityCommonStockSharesOutstanding', b'WeightedAverageNumberOfDilutedSharesOutstanding')
    assert extract(raw)['status'] == 'UNAVAILABLE'


def test_inline_scale_and_commas():
    raw = filing().replace(b'xmlns:dei=', b'xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:dei=')
    raw = raw.replace(b'<dei:EntityCommonStockSharesOutstanding contextRef="c" unitRef="u">1234</dei:EntityCommonStockSharesOutstanding>',
                      b'<ix:nonFraction name="dei:EntityCommonStockSharesOutstanding" contextRef="c" unitRef="u" scale="3">1,234</ix:nonFraction>')
    assert extract(raw)['facts'][0]['value_decimal'] == '1234000'


def test_malformed_or_external_entity_documents_fail_closed():
    for raw in (b'not xml', b'<!DOCTYPE x [<!ENTITY y SYSTEM "file:///etc/passwd">]><x>&y;</x>'):
        assert extract(raw)['status'] == 'UNSUPPORTED_DOCUMENT'


def test_inline_custom_namespace_cannot_impersonate_dei():
    raw = filing().replace(b'http://xbrl.sec.gov/dei/2026', b'https://example.com/custom')
    assert extract(raw)['status'] == 'UNAVAILABLE'


def test_inline_unsupported_numeric_transform_is_not_guessed():
    raw = filing().replace(b'xmlns:dei=', b'xmlns:ix="http://www.xbrl.org/2013/inlineXBRL" xmlns:dei=')
    raw = raw.replace(b'<dei:EntityCommonStockSharesOutstanding contextRef="c" unitRef="u">1234</dei:EntityCommonStockSharesOutstanding>',
                      b'<ix:nonFraction name="dei:EntityCommonStockSharesOutstanding" contextRef="c" unitRef="u" format="ixt:num-comma-decimal">1.234,0</ix:nonFraction>')
    assert extract(raw)['status'] == 'UNAVAILABLE'


def test_custom_measure_named_shares_is_not_a_share_unit():
    raw = filing(unit='custom:shares').replace(b'xmlns:dei=', b'xmlns:custom="https://example.com/unit" xmlns:dei=')
    assert extract(raw)['status'] == 'UNAVAILABLE'
