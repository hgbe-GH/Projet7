#!/usr/bin/env python
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from openagenda_rag.ingestion import NORMALIZED_COLUMNS, OpenAgendaClient, prepare_events_dataset
from openagenda_rag.settings import load_fetch_settings


RAW_OUTPUT = ROOT / "data" / "raw" / "openagenda_events.json"
PARQUET_OUTPUT = ROOT / "data" / "processed" / "events.parquet"
MANIFEST_OUTPUT = ROOT / "data" / "processed" / "fetch_manifest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch and normalize public OpenAgenda events from the Opendatasoft mirror dataset."
    )
    parser.add_argument("--agenda-uid", help="Optional origin agenda UID filter")
    parser.add_argument("--search", help="Optional helper string to discover an origin agenda with scripts/find_agendas.py")
    parser.add_argument("--city", help="Optional city filter applied in the API query and rechecked after normalization")
    parser.add_argument("--start-date", help="Inclusive lower date bound in YYYY-MM-DD or ISO datetime format")
    parser.add_argument("--end-date", help="Inclusive upper date bound in YYYY-MM-DD or ISO datetime format")
    parser.add_argument("--category-field", help="Field used for local category filtering, for example keywords_fr")
    parser.add_argument(
        "--category-id",
        action="append",
        dest="category_ids",
        help="Repeatable category identifier filter",
    )
    parser.add_argument("--page-size", type=int, default=100, help="API page size for the public dataset (max 100)")
    return parser.parse_args()


def resolve_agenda_uid(client: OpenAgendaClient, agenda_uid: str | None, search: str | None) -> str:
    if agenda_uid:
        return agenda_uid
    if not search:
        raise ValueError("An agenda UID or search term is required.")

    agendas = client.search_agendas(search=search, size=10)
    if not agendas:
        raise ValueError(f"No agenda matched search={search!r}.")
    if len(agendas) > 1:
        candidates = [
            {
                "uid": agenda.get("uid") or agenda.get("id"),
                "title": agenda.get("title"),
                "official": agenda.get("official"),
            }
            for agenda in agendas
        ]
        raise ValueError(
            "Multiple agendas matched the search term. Re-run with --agenda-uid.\n"
            + json.dumps(candidates, ensure_ascii=True, indent=2)
        )
    return agendas[0].get("uid") or agendas[0].get("id")


def ensure_parent_dirs() -> None:
    RAW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PARQUET_OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def write_outputs(raw_events: list[dict], normalized_rows: list[dict], manifest: dict) -> None:
    ensure_parent_dirs()
    RAW_OUTPUT.write_text(json.dumps(raw_events, ensure_ascii=True, indent=2))
    if normalized_rows:
        table = pa.Table.from_pylist(normalized_rows)
    else:
        table = pa.table({column: [] for column in NORMALIZED_COLUMNS})
    pq.write_table(table, PARQUET_OUTPUT)
    MANIFEST_OUTPUT.write_text(json.dumps(manifest, ensure_ascii=True, indent=2))


def main() -> int:
    args = parse_args()
    settings = load_fetch_settings()

    agenda_uid_arg = args.agenda_uid or settings.agenda_uid
    agenda_search = args.search or settings.agenda_search
    city = args.city if args.city is not None else settings.city
    start_date = args.start_date or settings.start_date
    end_date = args.end_date if args.end_date is not None else settings.end_date
    category_field = args.category_field if args.category_field is not None else settings.category_field
    category_ids = args.category_ids if args.category_ids is not None else settings.category_ids

    try:
        client = OpenAgendaClient(
            base_url=settings.opendatasoft_base_url,
            dataset=settings.opendatasoft_dataset,
        )
        agenda_uid = resolve_agenda_uid(client, agenda_uid=agenda_uid_arg, search=agenda_search) if (
            agenda_uid_arg or agenda_search
        ) else None
        raw_events = client.fetch_events(
            agenda_uid=agenda_uid,
            city=city,
            start_date=start_date,
            end_date=end_date,
            category_field=category_field,
            category_ids=category_ids or None,
            page_size=args.page_size,
        )
        normalized_rows = prepare_events_dataset(
            raw_events,
            agenda_uid=agenda_uid,
            city=city,
            category_field=category_field,
            category_ids=category_ids or None,
        )
    except Exception as exc:  # pragma: no cover - integration CLI
        print(f"OpenAgenda fetch failed: {exc}", file=sys.stderr)
        return 1

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "provider": "opendatasoft",
            "base_url": settings.opendatasoft_base_url,
            "dataset": settings.opendatasoft_dataset,
        },
        "agenda_uid": agenda_uid,
        "raw_event_count": len(raw_events),
        "normalized_event_count": len(normalized_rows),
        "filters": {
            "search": agenda_search,
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "category_field": category_field,
            "category_ids": category_ids,
        },
        "outputs": {
            "raw_json": str(RAW_OUTPUT.relative_to(ROOT)),
            "parquet": str(PARQUET_OUTPUT.relative_to(ROOT)),
            "manifest": str(MANIFEST_OUTPUT.relative_to(ROOT)),
        },
    }
    write_outputs(raw_events, normalized_rows, manifest)

    frame = pd.DataFrame(normalized_rows)
    print(
        json.dumps(
            {
                "agenda_uid": agenda_uid,
                "raw_event_count": len(raw_events),
                "normalized_event_count": len(normalized_rows),
                "source": manifest["source"],
                "columns": frame.columns.tolist(),
                "outputs": manifest["outputs"],
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
