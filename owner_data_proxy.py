"""Owner-authenticated read-only bridge to the existing Zion data service.

No DCF session or server credential confers data access. The source validates the
incoming owner's bearer and retains its object bounds, rights and release checks.
"""

import asyncio
import json
import re
from urllib.parse import parse_qsl, urlsplit

PREFIX = '/api/data/'
PRIVATE_PREFIX = '/private/v1/'
_READ_ROUTES = frozenset({
    'datasets', 'datasets/catalog', 'datasets/financial-query', 'capabilities', 'equity-claims',
    'readiness', 'readiness/screen', 'historical-series', 'stock-history',
    'financial-history', 'financial-history/batch', 'financial-companies', 'financial-metrics',
    'financial-coverage', 'financial-screen',
    'research-overview', 'research-identity', 'research-prices', 'research-valuation',
    'research-peers', 'research-certification', 'research-screen',
})
_DATASET_PATH = re.compile(
    r'datasets/(?:catalog/[a-f0-9]{32}|[a-z]+/(?:objects|object|schema|rows))\Z'
)
_RESPONSE_HEADERS = (
    'content-type', 'content-length', 'content-range', 'etag', 'accept-ranges',
    'x-data-quality', 'x-request-id',
)
_PRIVATE_HEADERS = {
    'cache-control': 'private, no-store',
    'vary': 'Authorization',
    'x-content-type-options': 'nosniff',
}


class Rejected(ValueError):
    def __init__(self, code, status):
        self.code, self.status = code, status
        super().__init__(code)


def request_plan(request):
    """Validate the bounded route/query and select only caller-owned headers."""
    if request.method not in ('GET', 'HEAD'):
        raise Rejected('READ_ONLY', 405)
    auth = request.headers.get('authorization') or ''
    if len(auth) > 4096 or not re.fullmatch(r'Bearer [A-Za-z0-9._~+/-]+=*', auth):
        raise Rejected('OWNER_BEARER_REQUIRED', 401)
    if re.search(r'[\x00-\x20\x7f]', request.url):
        raise Rejected('INVALID_URL', 400)
    url = urlsplit(request.url)
    prefix = next((p for p in (PREFIX, PRIVATE_PREFIX) if url.path.startswith(p)), None)
    if prefix is None:
        raise Rejected('NOT_FOUND', 404)
    route = url.path.removeprefix(prefix)
    if route == 'catalog':
        route = 'datasets/catalog'
    if route not in _READ_ROUTES and not _DATASET_PATH.fullmatch(route):
        raise Rejected('NOT_FOUND', 404)
    if len(url.query) > 8192 or re.search(r'%(?![a-fA-F0-9]{2})', url.query):
        raise Rejected('INVALID_PARAMETER', 400)
    try:
        pairs = parse_qsl(url.query, keep_blank_values=True, strict_parsing=True,
                          max_num_fields=32, errors='strict')
    except (ValueError, UnicodeError):
        raise Rejected('INVALID_PARAMETER', 400) from None
    seen = set()
    for key, value in pairs:
        if (key in seen or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', key)
                or key in {'url', 'origin', 'host', 'headers', 'authorization', 'token',
                           'bearer', 'principal', 'service_token', 'api_key'}
                or len(value) > 4096 or re.search(r'[\x00-\x1f\x7f]', value)):
            raise Rejected('INVALID_PARAMETER', 400)
        seen.add(key)
    # Preserve the exact validated query and bearer; only the binding chooses the host.
    target = 'https://zion.internal/private/v1/' + route
    if url.query:
        target += '?' + url.query
    headers = {'authorization': auth}
    for key in ('if-match', 'range'):
        value = request.headers.get(key)
        if value:
            if len(value) > 512 or re.search(r'[\x00-\x1f\x7f]', value):
                raise Rejected('INVALID_HEADER', 400)
            headers[key] = value
    return target, headers


async def handle(request, env):
    """Stream authenticated source bytes without transforming private data."""
    from workers import Request, Response

    headers = dict(_PRIVATE_HEADERS)
    try:
        target, forwarded = request_plan(request)
        binding = getattr(env, 'ZION_FINANCIAL_QUERY', None)
        if binding is None:
            raise Rejected('DATA_SERVICE_UNAVAILABLE', 503)
        upstream = Request(target, method=request.method, headers=forwarded, redirect='manual')
        async with asyncio.timeout(30):
            response = await binding.fetch(upstream.js_object)
        if 300 <= response.status < 400:
            raise Rejected('SOURCE_REDIRECT_REFUSED', 502)
        for key in _RESPONSE_HEADERS:
            value = response.headers.get(key)
            if value:
                headers[key] = value
        return Response(None if request.method == 'HEAD' else response.body,
                        status=response.status, headers=headers)
    except Rejected as error:
        code, status = error.code, error.status
    except Exception:
        code, status = 'DATA_SERVICE_UNAVAILABLE', 503
    headers['content-type'] = 'application/json'
    if status == 401:
        headers['www-authenticate'] = 'Bearer'
    if status == 405:
        headers['allow'] = 'GET, HEAD'
    return Response(None if request.method == 'HEAD' else json.dumps({'error': {'code': code}}),
                    status=status, headers=headers)
