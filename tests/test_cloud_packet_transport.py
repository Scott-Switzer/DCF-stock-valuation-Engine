"""Check immutable artifact transport without loading the cloud SDK or financial data."""
import ast
import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace


def test_packet_content_address_survives_later_rebuild():
    source = Path('deploy/valuation-completion/packet_worker.py').read_text()
    tree = ast.parse(source)
    functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in {'sha', 'immutable'}]
    scope = {'hashlib': hashlib, 'json': json, 'OUT': 'synthetic/'}
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<packet-transport>', 'exec'), scope)
    objects = {}

    async def put(key, raw):
        objects[key] = raw

    env = SimpleNamespace(DATA=SimpleNamespace(put=put))
    first = asyncio.run(scope['immutable'](env, 'packets', {'revision': 1}))
    second = asyncio.run(scope['immutable'](env, 'packets', {'revision': 2}))
    assert first['key'] != second['key']
    assert json.loads(objects[first['key']]) == {'revision': 1}
    assert hashlib.sha256(objects[first['key']].encode()).hexdigest() == first['sha256']
