import io
import json
import zipfile
from types import SimpleNamespace
import pytest
from dcf_loader import ProviderError
from scripts.ppe_cloud_source import SecArchive, S3Transport


class ArchiveClient:
    def __init__(self, cik=789019):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('CIK0000789019.json', json.dumps({'cik': cik, 'facts': {}}))
        self.raw = stream.getvalue()
        self.reads = []

    def head_object(self, **kw):
        return {'ContentLength': len(self.raw), 'ETag': '"pinned"'}

    def get_object(self, **kw):
        self.reads.append(kw)
        assert kw['IfMatch'] == '"pinned"'
        start, end = map(int, kw['Range'].removeprefix('bytes=').split('-'))
        return {'Body': io.BytesIO(self.raw[start:end+1])}


def test_archive_pins_every_range_and_verifies_identity():
    client = ArchiveClient()
    archive = SecArchive(client, 'private', 'sec/bulk/published/companyfacts.zip')
    facts, source = archive.facts('0000789019')
    assert facts['cik'] == 789019
    assert len(source['sha256']) == 64
    assert source['archive_etag'] == 'pinned'
    assert all('Range' in r for r in client.reads)
    assert archive.facts('0000000001') == (None, None)
    archive.close()


def test_archive_wrong_issuer_rejected():
    archive = SecArchive(ArchiveClient(1), 'private', 'sec/bulk/published/companyfacts.zip')
    with pytest.raises(ProviderError, match='issuer'):
        archive.facts('0000789019')
    archive.close()


def test_transport_cannot_read_or_write_other_financial_namespaces():
    transport = S3Transport(SimpleNamespace())
    for op in ['get', 'put']:
        with pytest.raises(ProviderError, match='namespace'):
            transport.call(op, 'private/research.json', raw=b'{}')
