#!/usr/bin/env python
from __future__ import annotations

import argparse
import json

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Functional test script for the local OpenAgenda RAG API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL of the local API")
    parser.add_argument("--question", default="Je cherche un concert a Paris", help="Question sent to /ask")
    parser.add_argument("--include-rebuild", action="store_true", help="Also call /rebuild")
    parser.add_argument("--admin-token", help="Optional admin token sent to /rebuild via X-Admin-Token")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    timeout = httpx.Timeout(120.0)

    with httpx.Client(base_url=args.base_url, timeout=timeout) as client:
        health = client.get("/health")
        ask = client.post("/ask", json={"question": args.question})

        payload = {
            "health_status": health.status_code,
            "health_body": health.json(),
            "ask_status": ask.status_code,
            "ask_body": ask.json(),
        }

        if args.include_rebuild:
            headers = {"X-Admin-Token": args.admin_token} if args.admin_token else {}
            rebuild = client.post("/rebuild", json={}, headers=headers)
            payload["rebuild_status"] = rebuild.status_code
            payload["rebuild_body"] = rebuild.json()

    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
