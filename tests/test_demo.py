from __future__ import annotations

from openagenda_rag.demo import DemoScenario, run_demo


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def json(self) -> dict:
        return self._payload


class FakeClient:
    def get(self, path: str) -> FakeResponse:
        assert path == "/health"
        return FakeResponse(200, {"status": "ok"})

    def post(self, path: str, json: dict) -> FakeResponse:
        assert path == "/ask"
        answer = (
            "Concert Fishers a Paris."
            if "Fishers" in json["question"]
            else "Je ne sais pas, le corpus est limite a Paris."
        )
        return FakeResponse(200, {"answer": answer, "sources": []})


def test_run_demo_executes_nominal_and_edge_cases_under_limit():
    clock = iter([10.0, 42.0])
    result = run_demo(
        client=FakeClient(),
        scenarios=[
            DemoScenario("nominal", "Parle-moi de Concert Fishers a Paris"),
            DemoScenario("limite", "Quelles expositions photo a Lyon ?"),
        ],
        max_seconds=300,
        monotonic=lambda: next(clock),
    )

    assert result["duration_seconds"] == 32.0
    assert [item["case_id"] for item in result["scenarios"]] == [
        "nominal",
        "limite",
    ]
    assert result["within_limit"] is True


def test_run_demo_timer_starts_before_health_check():
    clock = iter([10.0, 12.5])

    result = run_demo(
        client=FakeClient(),
        scenarios=[DemoScenario("nominal", "Question")],
        max_seconds=300,
        monotonic=lambda: next(clock),
    )

    assert result["duration_seconds"] == 2.5


def test_run_demo_marks_duration_over_five_minutes():
    clock = iter([0.0, 301.0])
    result = run_demo(
        client=FakeClient(),
        scenarios=[DemoScenario("nominal", "Question")],
        max_seconds=300,
        monotonic=lambda: next(clock),
    )

    assert result["within_limit"] is False
