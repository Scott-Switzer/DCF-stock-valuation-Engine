import io
import json
import zipfile
from types import SimpleNamespace
import pytest
from dcf_loader import ProviderError
from scripts.ppe_cloud_source import CandidateTransport, SecArchive, S3Transport


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


class MemoryClient:
    """In-memory S3 stand-in with ETag + conditional-write semantics."""

    class _NoSuchKey(Exception):
        pass

    class _ClientError(Exception):
        def __init__(self, code):
            super().__init__(code)
            self.response = {"Error": {"Code": code}}

    def __init__(self):
        self.objects = {}
        self.exceptions = SimpleNamespace(NoSuchKey=self._NoSuchKey,
                                          ClientError=self._ClientError)

    def get_object(self, Bucket, Key):
        if Key not in self.objects:
            raise self._NoSuchKey(Key)
        body, etag = self.objects[Key]
        return {"Body": io.BytesIO(body), "ContentLength": len(body), "ETag": etag}

    def put_object(self, Bucket, Key, Body, ContentType, **conditions):
        current = self.objects.get(Key)
        if "IfMatch" in conditions:
            if current is None or current[1] != conditions["IfMatch"]:
                raise self._ClientError("PreconditionFailed")
        if "IfNoneMatch" in conditions and current is not None:
            raise self._ClientError("PreconditionFailed")
        etag = f'"{len(Body):x}"'
        self.objects[Key] = (Body, etag)
        return {"ETag": etag}


def test_candidate_transport_refuses_production_pointer_writes():
    transport = CandidateTransport(MemoryClient())
    with pytest.raises(ProviderError, match="production pointer"):
        transport.call("put", "control/valuation/CURRENT.json", raw=b"{}")
    with pytest.raises(ProviderError, match="never the production pointer"):
        CandidateTransport(MemoryClient(), pointer="control/valuation/CURRENT.json")
    with pytest.raises(ProviderError, match="never the production pointer"):
        CandidateTransport(MemoryClient(), pointer="control/valuation/EVIL.json")


def test_candidate_transport_merges_preserving_existing_entries():
    client = MemoryClient()
    prior = {"schema_version": "ppe-valuation-index-v1", "companies": {
        "PEP": {"key": "gold/valuation/releases/" + "a" * 64 + "/companies/PEP.json",
                  "sha256": "a" * 64}}}
    client.objects[CandidateTransport.DEFAULT_POINTER] = (json.dumps(prior).encode(), '"v1"')
    transport = CandidateTransport(client)
    index = transport.get(CandidateTransport.DEFAULT_POINTER)
    assert set(index["companies"]) == {"PEP"}
    merged = {**index["companies"],
              "CAT": {"key": "gold/valuation/releases/" + "b" * 64 + "/companies/CAT.json",
                        "sha256": "b" * 64}}
    transport.call("put", transport.pointer,
                   json.dumps({**index, "companies": merged}).encode(),
                   expected_etag=transport.etags[transport.pointer])
    again = transport.get(CandidateTransport.DEFAULT_POINTER)
    assert set(again["companies"]) == {"PEP", "CAT"}
    # Stale ETag on a concurrent update fails instead of clobbering.
    with pytest.raises(ProviderError):
        transport.call("put", transport.pointer, b"{}", expected_etag='"v1"')
    assert set(transport.get(CandidateTransport.DEFAULT_POINTER)["companies"]) == {"PEP", "CAT"}


def test_etag_recorded_only_by_get_not_bare_call():
    # Regression trap: conditional pointer updates must source the ETag from
    # get() (which records it), not from a bare call() (which does not).
    client = MemoryClient()
    client.objects[CandidateTransport.DEFAULT_POINTER] = (b"{}", '"v1"')
    transport = CandidateTransport(client)
    transport.call("get", CandidateTransport.DEFAULT_POINTER)
    assert transport.etags.get(CandidateTransport.DEFAULT_POINTER) is None
    transport.get(CandidateTransport.DEFAULT_POINTER)
    assert transport.etags.get(CandidateTransport.DEFAULT_POINTER) == '"v1"'


def test_pointer_integrity_distinguishes_raw_identity_from_semantics():
    import hashlib
    from scripts.publish_candidate_packets import pointer_integrity
    a = b'{"companies": {"PEP": 1}}'
    b = b'{ "companies" : { "PEP" : 1 } }'
    raw_a, canon_a = pointer_integrity(a)
    raw_b, canon_b = pointer_integrity(b)
    # Same semantic content, different bytes: raw identity sees the change,
    # the canonical comparison does not, so it must never gate untouched-ness.
    assert raw_a != raw_b
    assert canon_a == canon_b
    assert raw_a == hashlib.sha256(a).hexdigest()
    assert pointer_integrity(None) == (None, None)
    raw, canon = pointer_integrity(b"not json")
    assert raw == hashlib.sha256(b"not json").hexdigest()
    assert canon is None


def test_corrupt_member_is_a_reportable_provider_error(monkeypatch):
    archive = SecArchive(ArchiveClient(), 'private', 'sec/bulk/published/companyfacts.zip')
    def corrupt(*args):
        raise zipfile.BadZipFile('CRC mismatch')
    monkeypatch.setattr(archive.archive, 'read', corrupt)
    with pytest.raises(ProviderError, match='member CRC'):
        archive.facts('0000789019')
    archive.close()
