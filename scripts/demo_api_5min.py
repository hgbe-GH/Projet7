from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from time import monotonic, sleep

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from openagenda_rag.demo import DemoScenario, run_demo  # noqa: E402

SCENARIOS = [
    DemoScenario("nominal", "Parle-moi de Concert Fishers a Paris"),
    DemoScenario("limite", "Quelles expositions photo a Lyon ?"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run and time the two-scenario OpenAgenda API demonstration."
    )
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--max-seconds", type=float, default=300.0)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument(
        "--ensure-compose",
        action="store_true",
        help="Start the Docker Compose API before timing health and questions.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=PROJECT_ROOT / "outputs/demo/demo_api_timing.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = monotonic()
    if args.ensure_compose:
        try:
            existing = httpx.get(
                f"{args.base_url.rstrip('/')}/health",
                timeout=2,
            )
            existing.raise_for_status()
        except httpx.HTTPError:
            subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=PROJECT_ROOT,
                check=True,
            )

    with httpx.Client(base_url=args.base_url, timeout=args.timeout) as client:
        for attempt in range(60):
            try:
                payload = run_demo(
                    client=client,
                    scenarios=SCENARIOS,
                    max_seconds=args.max_seconds,
                    started_at=started,
                )
                break
            except httpx.HTTPError:
                if attempt == 59:
                    raise
                sleep(1)

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    for scenario in payload["scenarios"]:
        print(f"\n[{scenario['case_id']}] {scenario['question']}")
        print(scenario["answer"])
        print(f"Sources: {len(scenario['sources'])}")
    print(
        f"\nDuree mesuree: {payload['duration_seconds']:.3f} s "
        f"(limite: {payload['max_seconds']:.0f} s)"
    )
    print(f"Rapport: {args.output_path}")
    return 0 if payload["within_limit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
