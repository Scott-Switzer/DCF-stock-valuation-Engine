"""The benchmark leg reaches its sibling Worker over a service binding.

A Worker's subrequest to another Worker's public hostname on the same zone is refused by
the edge with a plain-text `error code: 1042`, which reached the DCF benchmark provider as
a non-JSON body (`Expecting value: line 1 column 1 (char 0)`). A deployment that carries
the binding must therefore resolve assumptions without any public origin, exactly as the
equity-claims leg already did.
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as app_module  # noqa: E402
import zion_equity_claims_service as service  # noqa: E402

# The benchmark leg must bind to the benchmark Worker; binding it to the financial query
# Worker answered `INVALID_REQUEST: unsupported operation` instead of an assumption row.
assert service.BENCHMARK_BINDING_NAME == "ZION_BENCHMARK_QUERY"

RELEASE = "11c1e6bb76d9db12feeec3e3949a9ffe370d0ace87f3047aaac66f431270ccc9"
SUBJECT = "Computers/Peripherals"
VALUE = "0.09344048072400105"


def payload():
    return {
        "schema_version": "zion-private-query-v1",
        "request_id": "binding-test",
        "operation": "benchmark_context",
        "release": {
            "serving_release_id": "ddfi-benchmarks:" + RELEASE,
            "ddfi_release_id": RELEASE,
            "dataset_id": "cost_of_capital",
            "region": "US",
            "published_at": "2026-01-12",
            "provider": "NYU Stern / Aswath Damodaran",
        },
        "coverage": {},
        "data": {
            "observations": [{
                "subject": SUBJECT,
                "measure": "wacc",
                "classification": "BENCHMARK_ASSUMPTION_NOT_COMPANY_FACT",
                "value_decimal": VALUE,
                "unit": "decimal",
            }]
        },
    }


def selection():
    return {"wacc": {"release_id": RELEASE, "subject": SUBJECT, "measure": "wacc",
                     "mode": "current", "source": "zion"}}


def today():
    return datetime.now(timezone.utc).date().isoformat()


class IncomingResponse:
    """The subset of a Cloudflare Response the transport reads from the binding."""

    def __init__(self, status, body):
        self.status = status
        self._body = body

    async def text(self):
        return self._body


class CapturingTransport(service.ServiceBindingHTTP):
    """The runtime step only: records the prepared request, answers with the contract."""

    def __init__(self, payload, sent):
        super().__init__(object())
        self.payload, self.sent = payload, sent

    async def dispatch(self, target, headers, body=None):
        self.sent.update(target=target, headers=headers, body=body)
        return IncomingResponse(200, json.dumps(self.payload))


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch, tmp_path):
    monkeypatch.setenv("DCF_STATE_PATH", str(tmp_path / "library.sqlite3"))
    app_module.app.config.update(TESTING=True, STATE_PATH=str(tmp_path / "state.sqlite3"))


def test_bound_deployment_resolves_a_benchmark_without_any_public_origin(monkeypatch):
    sent = {}
    contract = payload()
    monkeypatch.setattr(service, "ServiceBindingHTTP",
                        lambda binding, **kwargs: CapturingTransport(contract, sent))
    bound = []
    monkeypatch.setattr(service, "service_binding",
                        lambda name=service.BINDING_NAME: bound.append(name) or object())
    monkeypatch.setattr(service, "sync", lambda awaitable: asyncio.run(awaitable))
    monkeypatch.setenv("ZION_BENCHMARK_TOKEN", "scoped-benchmark-bearer")
    for name in ("ZION_BENCHMARK_BASE_URL", "ZION_HISTORY_BASE_URL", "ZION_HISTORY_TOKEN"):
        monkeypatch.delenv(name, raising=False)

    resolved = app_module.resolve_benchmark_selections(selection(), today())

    assert bound == [service.BENCHMARK_BINDING_NAME]
    assert resolved["wacc"]["value_decimal"] == VALUE
    assert resolved["wacc"]["release_id"] == RELEASE
    assert resolved["wacc"]["measure"] == "wacc"
    # The binding ignores the host, so the leg carries the internal origin and no public one.
    assert sent["target"] == service.BINDING_ORIGIN + "/private/v1/query"
    assert sent["headers"]["Authorization"] == "Bearer scoped-benchmark-bearer"
    assert json.loads(sent["body"]) == {"operation": "benchmark_context", "release_id": RELEASE,
                                       "subject": SUBJECT, "measures": ["wacc"]}


def test_without_a_binding_the_public_origin_is_still_required(monkeypatch):
    monkeypatch.setattr(service, "service_binding", lambda name=service.BINDING_NAME: None)
    monkeypatch.setenv("ZION_BENCHMARK_TOKEN", "scoped-benchmark-bearer")
    for name in ("ZION_BENCHMARK_BASE_URL", "ZION_HISTORY_BASE_URL"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValueError, match="not configured in this runtime"):
        app_module.resolve_benchmark_selections(selection(), today())
