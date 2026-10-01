from argparse import Namespace
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import httpx
import pytest


def test_demo_stops_after_provider_failure_instead_of_repeating_calls(monkeypatch, tmp_path):
    path = Path(__file__).resolve().parents[1] / "scripts/demo_api_5min.py"
    spec = importlib.util.spec_from_file_location("demo_cli", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args = Namespace(base_url="http://localhost:8000", timeout=1, max_seconds=300,
                     ensure_compose=False, output_path=tmp_path / "result.json")
    monkeypatch.setattr(module, "parse_args", lambda: args)
    client = MagicMock()
    request = httpx.Request("POST", "http://localhost:8000/ask")
    response = httpx.Response(503, request=request)
    error = httpx.HTTPStatusError("Unavailable", request=request, response=response)
    client.post.side_effect = error
    context_manager = MagicMock()
    context_manager.__enter__.return_value = client
    monkeypatch.setattr(module.httpx, "Client", lambda **kwargs: context_manager)
    # Avoid waiting while exposing the original repeated-call bug.
    monkeypatch.setattr(module, "sleep", lambda seconds: None, raising=False)

    with pytest.raises(httpx.HTTPStatusError):
        module.main()

    assert client.post.call_count == 1
    assert not args.output_path.exists()
