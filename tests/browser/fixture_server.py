"""Local-only deterministic browser server. Never deployed in the Worker."""
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from app import app  # noqa: E402
from test_effective_assumptions import frozen_scenario  # noqa: E402
import auto_loading  # noqa: E402
import requests  # noqa: E402
from dcf_loader import ProviderError  # noqa: E402

original_load = auto_loading.load_method

def frozen_load(method, ticker, *args, **kwargs):
    if method != 'dcf' or ticker != 'DEMO':
        raise ProviderError('Browser fixture supports DEMO DCF only.')
    return original_load(method, ticker, snapshot=frozen_scenario(),
                         tax_override=kwargs.get('tax_override'), tax_scenario=kwargs.get('tax_scenario'))


def no_network(*args, **kwargs):
    raise ProviderError('External providers disabled in deterministic browser acceptance.')


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='dcf-browser-') as directory:
        os.environ['DCF_STATE_PATH'] = str(Path(directory) / 'research.sqlite3')
        app.config.update(STATE_PATH=str(Path(directory) / 'limits.sqlite3'), TESTING=True)
        auto_loading.load_method = frozen_load
        requests.sessions.Session.request = no_network
        app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '5179')), debug=False, threaded=True)
