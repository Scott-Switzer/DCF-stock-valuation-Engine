"""Bounded, read-only SEC ZIP access and conditional valuation publication.

This optional operator transport uses boto3, never runs in the public Worker,
and never downloads the bulk ZIP. Credentials stay in the configured S3 client.
"""
import base64
import hashlib
import io
import json
import re
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor

from dcf_loader import ProviderError

MAX_FACTS = 16 * 1024 * 1024


class RangeReader(io.RawIOBase):
    def __init__(self, client, bucket, key):
        self.client, self.bucket, self.key = client, bucket, key
        head = client.head_object(Bucket=bucket, Key=key)
        self.size, self.etag, self.position = head['ContentLength'], head['ETag'], 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if whence not in (0, 1, 2) or position < 0:
            raise ProviderError('Invalid SEC archive offset.')
        self.position = position
        return position

    def read(self, size=-1):
        size = min(self.size - self.position, size if size >= 0 else self.size)
        if size <= 0:
            return b''
        if size > MAX_FACTS:
            raise ProviderError('SEC archive range exceeds budget.')
        obj = self.client.get_object(Bucket=self.bucket, Key=self.key,
            Range=f'bytes={self.position}-{self.position + size - 1}', IfMatch=self.etag)
        try:
            raw = obj['Body'].read(size + 1)
        finally:
            obj['Body'].close()
        if len(raw) != size:
            raise ProviderError('SEC archive range length mismatch.')
        self.position += len(raw)
        return raw


class SecArchive:
    def __init__(self, client, bucket, key):
        if not re.fullmatch(r'sec/bulk/[A-Za-z0-9_-]+/companyfacts\.zip', key):
            raise ProviderError('Expected a published SEC companyfacts ZIP key.')
        self.reader = RangeReader(client, bucket, key)
        self.archive = zipfile.ZipFile(self.reader)

    def facts(self, cik):
        member = f'CIK{cik}.json'
        try:
            entry = self.archive.getinfo(member)
        except KeyError:
            return None, None
        if entry.file_size > MAX_FACTS or entry.compress_size > MAX_FACTS:
            raise ProviderError('SEC companyfacts member exceeds budget.')
        try:
            raw = self.archive.read(entry)  # zipfile verifies the member CRC.
        except (zipfile.BadZipFile, zlib.error, EOFError):
            raise ProviderError('SEC archive member CRC or structure verification failed.') from None
        facts = json.loads(raw)
        if str(facts.get('cik', '')).zfill(10) != cik:
            raise ProviderError('SEC archive issuer mismatch.')
        return facts, {
            'provider': 'SEC companyfacts',
            'url': f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
            'sha256': hashlib.sha256(raw).hexdigest(),
            'archive_key': self.reader.key,
            'archive_etag': self.reader.etag.strip('"'),
            'archive_member': member,
            'archive_member_crc32': f'{entry.CRC:08x}',
        }

    def close(self):
        self.archive.close()


class S3Transport:
    """Existing publisher protocol; writes restricted to valuation objects."""
    def __init__(self, client, bucket='financial-system-datasets'):
        self.client, self.bucket, self.etags = client, bucket, {}

    def call(self, op, key='', raw=None, expected_etag=None, items=None):
        if op == 'batch':
            if len(items) > 4:
                raise ProviderError('Publisher batch exceeds budget.')
            def execute(item):
                return self.call(item['op'], item['key'],
                    raw=base64.b64decode(item['body']) if 'body' in item else None)
            with ThreadPoolExecutor(max_workers=4) as executor:
                return list(executor.map(execute, items))
        if op == 'get':
            if not (key in {'gold/serving/coverage25/CURRENT.json', 'control/valuation/CURRENT.json'}
                    or re.fullmatch(r'gold/valuation/releases/[a-f0-9]{64}/companies/[A-Z0-9.-]+\.json', key)
                    or re.fullmatch(r'gold/serving/releases/[a-f0-9]+/(manifest\.json|identity/resolver_index\.json|entities/entity_sec_cik_[0-9]+(?:_[A-Z-]+)?/fundamentals/annual\.json)', key)):
                raise ProviderError('Publisher read outside allowed namespace.')
            try:
                obj = self.client.get_object(Bucket=self.bucket, Key=key)
            except self.client.exceptions.NoSuchKey:
                return None
            try:
                if obj['ContentLength'] > MAX_FACTS:
                    raise ProviderError('Publisher object exceeds budget.')
                body = obj['Body'].read(MAX_FACTS + 1)
            finally:
                obj['Body'].close()
            if len(body) > MAX_FACTS:
                raise ProviderError('Publisher object exceeds budget.')
            return {'body': base64.b64encode(body).decode(), 'etag': obj['ETag']}
        if op != 'put' or not (key == 'control/valuation/CURRENT.json' or re.fullmatch(
                r'gold/valuation/releases/[a-f0-9]{64}/companies/[A-Z0-9.-]+\.json|raw/valuation-sec/[a-f0-9]{64}/companyfacts\.json', key)):
            raise ProviderError('Publisher write outside valuation namespace.')
        if len(raw) > (MAX_FACTS if key.startswith('raw/') else 524288):
            raise ProviderError('Publisher write exceeds budget.')
        condition = {'IfMatch': expected_etag} if expected_etag else {'IfNoneMatch': '*'}
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=raw,
                ContentType='application/json', **condition)
        except self.client.exceptions.ClientError as exc:
            if key == 'control/valuation/CURRENT.json' or exc.response['Error']['Code'] not in {'PreconditionFailed', '412'}:
                raise ProviderError('Conditional valuation publication failed.') from None
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        try:
            checked = obj['Body'].read(len(raw) + 1)
        finally:
            obj['Body'].close()
        if checked != raw:
            raise ProviderError('Published valuation read-back mismatch.')
        return {'key': key, 'bytes': len(raw)}

    def get(self, key, digest=None):
        result = self.call('get', key)
        if result is None:
            return None
        self.etags[key] = result['etag']
        raw = base64.b64decode(result['body'])
        if digest and hashlib.sha256(raw).hexdigest() != digest:
            raise ProviderError('Immutable artifact hash mismatch.')
        return json.loads(raw)

    def close(self):
        pass


def rclone_client(remote):
    import configparser
    from pathlib import Path
    import boto3
    from botocore.config import Config
    config = configparser.ConfigParser(interpolation=None)
    config.read(Path.home() / '.config/rclone/rclone.conf')
    entry = config[remote]
    return boto3.client('s3', endpoint_url=entry['endpoint'],
        aws_access_key_id=entry['access_key_id'], aws_secret_access_key=entry['secret_access_key'],
        region_name='auto', config=Config(connect_timeout=5, read_timeout=30,
            retries={'max_attempts': 2, 'mode': 'standard'}))
