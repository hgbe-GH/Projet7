#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from openagenda_rag.ingestion import OpenAgendaClient
from openagenda_rag.settings import load_fetch_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search origin agendas in the public Opendatasoft OpenAgenda dataset.")
    parser.add_argument("--search", required=True, help="Substring matched against recent agenda titles and event titles")
    parser.add_argument("--size", type=int, default=10, help="Maximum number of agendas to return")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = load_fetch_settings()

    client = OpenAgendaClient(
        base_url=settings.opendatasoft_base_url,
        dataset=settings.opendatasoft_dataset,
    )
    agendas = client.search_agendas(search=args.search, size=args.size)
    simplified = []
    for agenda in agendas:
        simplified.append(
            {
                "uid": agenda.get("uid") or agenda.get("id"),
                "title": agenda.get("title"),
                "description": agenda.get("description"),
                "official": agenda.get("official"),
                "canonicalUrl": agenda.get("canonicalUrl") or agenda.get("url"),
            }
        )
    print(json.dumps(simplified, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
