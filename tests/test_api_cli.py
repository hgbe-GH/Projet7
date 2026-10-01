from argparse import Namespace
import importlib.util
from pathlib import Path

import httpx
import pytest


@pytest.mark.parametrize(
    "health_status, ask_status, rebuild_status, expected_exit",
    [(200, 200, None, 0), (503, 200, None, 1), (200, 503, None, 1), (200, 200, 503, 1)],
)
def test_api_test_cli_returns_failure_for_unsuccessful_endpoints(
    monkeypatch, capsys, health_status, ask_status, rebuild_status, expected_exit
):
    path = Path(__file__).resolve().parents[1] / "scripts/api_test.py"
    spec = importlib.util.spec_from_file_location("api_test_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args = Namespace(base_url="http://local", question="Concert", timeout=1,
                     include_rebuild=rebuild_status is not None, admin_token=None, rebuild_timeout=1)
    monkeypatch.setattr(module, "parse_args", lambda: args)

    def handle(request):
        statuses = {"/health": health_status, "/ask": ask_status, "/rebuild": rebuild_status}
        return httpx.Response(statuses[request.url.path], json={"status": "test"})

    real_client = httpx.Client
    monkeypatch.setattr(module.httpx, "Client", lambda **kwargs: real_client(
        **kwargs, transport=httpx.MockTransport(handle)))

    assert module.main() == expected_exit
    assert '"ask_status"' in capsys.readouterr().out
