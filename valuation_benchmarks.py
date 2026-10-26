"""Read-only consumer of PPE's immutable Damodaran assumption releases.

Publication metadata is additive: an optional ``publication_evidence.json``
catalog beside the releases binds ``published_at`` to preserved source evidence
(the provider's HTTP Last-Modified of the exact source bytes, held under an
evidence sha256). Download time and stated vintage are disclosed but never used
for availability, and historical cutoffs before supported availability stay
fail-closed: an unevidenced vintage is never backdated.
"""
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

VERSION='damodaran-assumptions-v1'
EVIDENCE_VERSION='damodaran-publication-evidence-v1'
TARGETS={
    'wacc_override':('wacc','fraction',False),
    'ebit_margins':('operating_margin','fraction',True),
    'tax_rates':('tax_rate','fraction',True),
    'net_income_margins':('net_margin','fraction',True),
}
# The only reviewed publication-evidence methods. SERVER_LAST_MODIFIED binds the
# publication date to the provider's own timestamp for the exact bytes.
PUBLICATION_METHODS={'SERVER_LAST_MODIFIED','PUBLISHER_STATED','FIRST_OBSERVED'}
AVAILABLE='AVAILABLE_FROM_PUBLISHED_AT'
UNAVAILABLE='UNKNOWN_UNLESS_PUBLICATION_EVIDENCE_SUPPLIED'


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def _http_date(value):
    try:
        parsed=parsedate_to_datetime(str(value))
    except (TypeError,ValueError):
        raise ValueError('publication evidence needs an HTTP Last-Modified date') from None
    if parsed.tzinfo is None:raise ValueError('HTTP Last-Modified date requires a timezone')
    return parsed


def _instant(value, *, field):
    try:
        parsed=datetime.fromisoformat(str(value).replace('Z','+00:00'))
    except (TypeError,ValueError):
        raise ValueError(f'{field} is not an ISO timestamp') from None
    if parsed.tzinfo is None:raise ValueError(f'{field} requires a timezone')
    return parsed


def _retrieval(value):
    """Return ``(date, instant_or_None)`` for a recorded download time.

    A date-only record carries day precision. It is never upgraded to an
    asserted instant, so callers can only compare it by day.
    """
    text=str(value)
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', text):
        try:
            return date.fromisoformat(text),None
        except ValueError:
            raise ValueError('retrieved_at is not a calendar date') from None
    instant=_instant(value,field='retrieved_at')
    return instant.date(),instant


def validate_publication(published_at, evidence, retrieved_at):
    """Validate publication metadata and return it in its recorded shape.

    A publication date is only usable for historical selection when it carries
    evidence that could have been observed at that date. A bare string, a guessed
    vintage label, download time, or an observation that precedes publication is
    rejected rather than stored.
    """
    if published_at is None:
        if evidence is not None:
            raise ValueError('publication evidence requires a publication date')
        return None
    published=date.fromisoformat(str(published_at))
    # Download time and evidence observation are independent collection events:
    # a catalog may bind bytes downloaded earlier to headers re-checked later.
    # Only the ordering that could fabricate a date is refused -- a publication
    # date before publication, or after the bytes were first downloaded.
    retrieval_date,retrieval_instant=_retrieval(retrieved_at)
    if published>retrieval_date:
        raise ValueError('publication date cannot follow retrieval')
    if not isinstance(evidence,dict):
        raise ValueError('publication date needs structured evidence')
    method=evidence.get('method')
    if method not in PUBLICATION_METHODS:
        raise ValueError('publication evidence method is not reviewed')
    url=urlparse(str(evidence.get('source_url') or ''))
    if url.scheme!='https' or not url.hostname:
        raise ValueError('publication evidence needs an https source URL')
    observed=_instant(evidence.get('observed_at'),field='evidence observed_at')
    if observed.date()<published:
        raise ValueError('publication evidence cannot be observed before publication')
    statement=str(evidence.get('statement') or '').strip()
    if not statement:
        raise ValueError('publication evidence needs the published statement')
    recorded={'method':method,'source_url':evidence['source_url'],
              'observed_at':observed.isoformat(),'statement':statement,
              'server_last_modified':None}
    if method=='SERVER_LAST_MODIFIED':
        modified=_http_date(evidence.get('server_last_modified'))
        if modified.date()!=published:
            raise ValueError('published_at must be the server Last-Modified date of the exact bytes')
        if retrieval_instant is not None and modified>retrieval_instant:
            raise ValueError('server Last-Modified cannot follow retrieval')
        recorded['server_last_modified']=str(evidence['server_last_modified'])
    return recorded


def load_publication_evidence(root):
    """Read the additive publication-evidence catalog beside the releases."""
    path=Path(root)/'publication_evidence.json'
    if not path.exists():
        return {}
    raw=path.read_bytes()
    if len(raw)>1048576:raise ValueError('Publication evidence budget exceeded')
    catalog=json.loads(raw)
    if catalog.get('schema_version')!=EVIDENCE_VERSION:
        raise ValueError('Publication evidence schema mismatch')
    entries=catalog.get('releases')
    if not isinstance(entries,list) or any(
        not isinstance(entry,dict) or not isinstance(entry.get('release_id'),str) for entry in entries
    ):
        raise ValueError('Publication evidence entries are malformed')
    if len({entry['release_id'] for entry in entries})!=len(entries):
        raise ValueError('Publication evidence entries are duplicated')
    return {entry['release_id']:entry for entry in entries}


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
    try:
        published_date=date.fromisoformat(str(published))
        observed=datetime.fromisoformat(str(evidence['observed_at']).replace('Z','+00:00'))
    except ValueError:
        return {'available':False,'published_at':published,'method':evidence.get('method'),
                'reason':'UNPARSEABLE_PUBLICATION_EVIDENCE'}
    if observed.date()<published_date:
        return {'available':False,'published_at':published,'method':evidence.get('method'),
                'reason':'EVIDENCE_PRECEDES_PUBLICATION'}
    return {'available':True,'published_at':published,'method':evidence['method'],
            'observed_at':evidence['observed_at'],'reason':None}

def _download_time(entry):
    """Return the catalog's disclosed download time.

    The curator writes ``download_retrieved_at`` (the name the evidence receipt
    and the PPE importer use); older hand-written catalogs and fixtures use
    ``retrieved_at``. Both are the same disclosed value and neither is ever used
    for availability, so accept either rather than depending on which writer
    produced the file. A catalog carrying neither stays unusable.
    """
    for key in ('retrieved_at','download_retrieved_at'):
        value=entry.get(key)
        if value is not None:
            return value
    return None


def resolve_publication(release, source_sha256, manifest_published_at, entry, manifest=None):
    """Resolve ``published_at`` from release metadata or byte-bound evidence.

    Anything that is not source evidence for these exact bytes fails closed:
    without a usable date the release stays unavailable at any historical
    cutoff instead of being backdated.
    """
    if manifest_published_at:
        status = publication_status(manifest or {})
        if status["available"]:
            return (str(manifest_published_at), (manifest or {}).get("publication_evidence"),
                    AVAILABLE)
        # A manifest date without reviewed evidence is not usable on its own, but
        # the catalog entry bound to these exact bytes can still supply it. Fall
        # through instead of refusing before the catalog is consulted.
    disclosed=(str(manifest_published_at),None,UNAVAILABLE) if manifest_published_at else (None,None,UNAVAILABLE)
    if not isinstance(entry,dict) or entry.get('source_sha256')!=source_sha256:
        return disclosed
    if entry.get('published_at') is None:
        return disclosed
    try:
        recorded=validate_publication(
            entry.get('published_at'),entry.get('publication_evidence'),_download_time(entry)
        )
    except ValueError:
        return disclosed
    return str(entry['published_at']),recorded,AVAILABLE


def _read_release(root, release):
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
    data=json.loads((path/'normalized.json').read_bytes())
    if (data.get('schema_version')!=VERSION or data.get('dataset_id')!=manifest.get('dataset_id')
            or data.get('region')!=manifest.get('region')):
        raise ValueError('Assumption metadata mismatch')
    return manifest,data


def load_benchmark(root, release, subject, measure, *, as_of=None, evidence=None):
    manifest,data=_read_release(root,release)
    published,publication_evidence,availability=resolve_publication(
        release,
        manifest.get('files',{}).get('source.bin'),
        manifest.get('published_at'),
        (load_publication_evidence(root) if evidence is None else evidence).get(release),
        manifest=manifest,
    )
    if as_of is not None:
        cutoff=date.fromisoformat(as_of)
        if availability != AVAILABLE or not published:
            reason=publication_status(manifest).get('reason') or 'NO_REVIEWED_PUBLICATION_EVIDENCE'
            raise ValueError('Benchmark vintage unavailable at historical cutoff: '+reason)
        if date.fromisoformat(published)>cutoff:
            raise ValueError('Benchmark vintage unavailable at historical cutoff: published after cutoff')
    selected=[r for r in data['records'] if r['subject']==subject and r['measure']==measure]
    if len(selected)!=1 or selected[0]['value_decimal'] is None:
        raise ValueError('Benchmark missing or ambiguous; select explicit industry/measure')
    row=deepcopy(selected[0])
    value=Decimal(row['value_decimal'])
    if not value.is_finite():raise ValueError('Nonfinite benchmark')
    if row.get('classification')!='BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT':
        raise ValueError('Benchmark is not a company fact')
    row.update(release_id=release,dataset_id=manifest['dataset_id'],region=manifest['region'],
               source_url=manifest['source_url'],published_at=published,
               publication_evidence=publication_evidence,historical_availability=availability,
               publication_method=(publication_evidence or {}).get("method"),
               selection_mode='HISTORICAL_PUBLISHED' if as_of else 'CURRENT_EXPLICIT_SELECTION')
    return row


def coverage_catalog(root, *, evidence=None):
    """Read-only coverage listing: each release's subject/measure pairs with its
    publication status. Selects nothing and writes nothing.
    """
    catalog=load_publication_evidence(root) if evidence is None else evidence
    listing=[]
    for path in sorted(Path(root).iterdir()):
        if not path.is_dir():
            continue
        manifest,data=_read_release(root,path.name)
        published,publication_evidence,availability=resolve_publication(
            path.name,
            manifest.get('files',{}).get('source.bin'),
            manifest.get('published_at'),
            catalog.get(path.name),
        )
        grouped={}
        for row in data['records']:
            grouped.setdefault((row.get('subject'),row.get('measure')),[]).append(row)
        # Only pairs a selection would actually serve are advertised as available.
        pairs=sorted(
            key for key,rows in grouped.items()
            if len(rows)==1 and rows[0].get('value_decimal') is not None
        )
        measures=sorted({measure for _,measure in pairs})
        listing.append({
            'release_id':path.name,
            'dataset_id':manifest['dataset_id'],
            'region':manifest['region'],
            'subjects':len({subject for subject,_ in pairs}),
            'measures':measures,
            'subject_measure_pairs':[{'subject':subject,'measure':measure} for subject,measure in pairs],
            'unavailable_pair_count':len(grouped)-len(pairs),
            'target_measures_available':sorted(set(measures)&{spec[0] for spec in TARGETS.values()}),
            'published_at':published,
            'publication_evidence':publication_evidence,
            'historical_availability':availability,
        })
    return listing


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
