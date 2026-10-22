"""Read-only consumer of PPE's immutable Damodaran assumption releases."""
from copy import deepcopy
from datetime import date
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

VERSION='damodaran-assumptions-v1'
TARGETS={
    'wacc_override':('wacc','fraction',False),
    'ebit_margins':('operating_margin','fraction',True),
    'tax_rates':('tax_rate','fraction',True),
    'net_income_margins':('net_margin','fraction',True),
}


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


PUBLICATION_METHODS={'PUBLISHER_STATED','FIRST_OBSERVED'}


def publication_status(manifest):
    """Report whether a release can be used for historical selection.

    A date alone is not evidence: a hand-edited manifest could carry any date.
    Historical mode requires a date plus recorded evidence whose method is
    reviewed and whose observation is dated, matching the importer contract.
    """
    published=manifest.get('published_at');evidence=manifest.get('publication_evidence')
    if not published:
        return {'available':False,'published_at':None,'method':None,
                'reason':'NO_PUBLICATION_DATE'}
    if not isinstance(evidence,dict) or evidence.get('method') not in PUBLICATION_METHODS:
        return {'available':False,'published_at':published,'method':None,
                'reason':'NO_REVIEWED_PUBLICATION_EVIDENCE'}
    if not evidence.get('observed_at') or not str(evidence.get('source_url','')).startswith('https://'):
        return {'available':False,'published_at':published,'method':evidence.get('method'),
                'reason':'INCOMPLETE_PUBLICATION_EVIDENCE'}
    return {'available':True,'published_at':published,'method':evidence['method'],
            'observed_at':evidence['observed_at'],'reason':None}


def load_benchmark(root, release, subject, measure, *, as_of=None):
    if not isinstance(release,str) or not re.fullmatch('[0-9a-f]{64}',release):
        raise ValueError('Exact assumption release hash required')
    path=Path(root)/release
    raw=(path/'manifest.json').read_bytes()
    if len(raw)>65536:raise ValueError('Manifest budget exceeded')
    manifest=json.loads(raw);identity=manifest.pop('release_id')
    if identity!=release or hashlib.sha256(encoded(manifest)).hexdigest()!=release or manifest.get('schema_version')!=VERSION:
        raise ValueError('Assumption release identity mismatch')
    for name in ['source.bin','normalized.json']:
        member=path/name
        if member.stat().st_size>4*1048576:raise ValueError('Assumption file budget exceeded')
        if hashlib.sha256(member.read_bytes()).hexdigest()!=manifest.get('files',{}).get(name):
            raise ValueError('Assumption source integrity mismatch')
    status=publication_status(manifest)
    if as_of is not None:
        cutoff=date.fromisoformat(as_of)
        if not status['available']:
            raise ValueError('Benchmark vintage unavailable at historical cutoff: '+status['reason'])
        if date.fromisoformat(manifest['published_at'])>cutoff:
            raise ValueError('Benchmark vintage unavailable at historical cutoff: published after cutoff')
    data=json.loads((path/'normalized.json').read_bytes())
    if (data.get('schema_version')!=VERSION or data.get('dataset_id')!=manifest.get('dataset_id')
            or data.get('region')!=manifest.get('region')):
        raise ValueError('Assumption metadata mismatch')
    selected=[r for r in data['records'] if r['subject']==subject and r['measure']==measure]
    if len(selected)!=1 or selected[0]['value_decimal'] is None:
        raise ValueError('Benchmark missing or ambiguous; select explicit industry/measure')
    row=deepcopy(selected[0])
    value=Decimal(row['value_decimal'])
    if not value.is_finite():raise ValueError('Nonfinite benchmark')
    if row.get('classification')!='BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT':
        raise ValueError('Benchmark is not a company fact')
    row.update(release_id=release,dataset_id=manifest['dataset_id'],region=manifest['region'],
               source_url=manifest['source_url'],published_at=manifest.get('published_at'),
               publication_method=status['method'],
               selection_mode='HISTORICAL_PUBLISHED' if as_of else 'CURRENT_EXPLICIT_SELECTION')
    return row


def apply_benchmarks(assumptions, selections):
    """Apply explicit selections to existing DCFAssumptions fields, preserving evidence."""
    result=deepcopy(assumptions);sources={}
    for target,row in selections.items():
        if target not in TARGETS:raise ValueError('Unsupported benchmark assumption target')
        if target in result and result[target] is not None:raise ValueError('Conflicting explicit assumption')
        measure,unit,annual=TARGETS[target]
        if row.get('measure')!=measure or row.get('unit')!=unit or not row.get('release_id'):
            raise ValueError('Incompatible benchmark measure/unit')
        value=Decimal(row['value_decimal'])
        if not value.is_finite():raise ValueError('Nonfinite benchmark')
        result[target]=[float(value)]*5 if annual else float(value)
        sources[target]=deepcopy(row)
    result['benchmark_sources']=sources
    return result
