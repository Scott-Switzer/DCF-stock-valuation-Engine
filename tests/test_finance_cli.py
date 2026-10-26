import importlib
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize('response,code', [
    ({'answer': 'PRIVATE_SENTINEL'}, 'BUNDLE_UNAVAILABLE'),
    ({'answer': 'PRIVATE_SENTINEL', 'bundle_id': 'b' * 64,
      'source_releases': {'SEC': 'one'}, 'data_as_of': None}, 'RELEASE_MISMATCH'),
])
def test_cli_rejects_untrusted_success_before_printing(monkeypatch, capsys, response, code):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'scripts'))
    finance = importlib.import_module('finance')
    monkeypatch.setattr(finance, 'request', lambda *a, **kw: response)
    monkeypatch.setattr(sys, 'argv', ['finance', 'WRDS coverage', '--bundle-id', 'a' * 64])
    with pytest.raises(SystemExit) as error:
        finance.main()
    assert error.value.code != 0
    output = capsys.readouterr()
    assert code in output.err
    assert 'PRIVATE_SENTINEL' not in output.out + output.err
