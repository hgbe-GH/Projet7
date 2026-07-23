from __future__ import annotations

from dataclasses import asdict, dataclass
from time import monotonic
from typing import Any, Callable


@dataclass(frozen=True)
class DemoScenario:
    case_id: str
    question: str


def run_demo(
    client: Any,
    scenarios: list[DemoScenario],
    max_seconds: float = 300.0,
    monotonic: Callable[[], float] = monotonic,
) -> dict[str, Any]:
    health = client.get("/health")
    health.raise_for_status()

    started = monotonic()
    results: list[dict[str, Any]] = []
    for scenario in scenarios:
        response = client.post("/ask", json={"question": scenario.question})
        response.raise_for_status()
        payload = response.json()
        answer = str(payload.get("answer") or "").strip()
        if not answer:
            raise RuntimeError(f"Scenario {scenario.case_id} returned an empty answer.")
        results.append(
            {
                **asdict(scenario),
                "answer": answer,
                "sources": payload.get("sources", []),
            }
        )

    duration = round(monotonic() - started, 3)
    return {
        "duration_seconds": duration,
        "max_seconds": max_seconds,
        "within_limit": duration < max_seconds,
        "scenarios": results,
    }
