from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import html
import json
from typing import Any
import re
import unicodedata

import requests


DEFAULT_BASE_URL = "https://public.opendatasoft.com/api/explore/v2.1"
DEFAULT_DATASET = "evenements-publics-openagenda"
DEFAULT_TIMEOUT = 30

NORMALIZED_COLUMNS = [
    "event_uid",
    "agenda_uid",
    "title",
    "summary",
    "long_description",
    "text_for_embedding",
    "city",
    "location_name",
    "latitude",
    "longitude",
    "first_timing",
    "last_timing",
    "timezone",
    "canonical_url",
    "categories",
    "source_updated_at",
    "raw_event",
]


def _normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    ascii_value = unicodedata.normalize("NFKD", value)
    ascii_value = ascii_value.encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r"\s+", " ", ascii_value).strip().lower()
    return ascii_value or None


def _coerce_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    if isinstance(value, dict):
        for key in ("fr", "en"):
            entry = value.get(key)
            if isinstance(entry, str) and entry.strip():
                return entry.strip()
        for entry in value.values():
            if isinstance(entry, str) and entry.strip():
                return entry.strip()
    return None


def _strip_html(value: str | None) -> str | None:
    if value is None:
        return None
    no_tags = re.sub(r"<[^>]+>", " ", value)
    unescaped = html.unescape(no_tags)
    normalized = re.sub(r"\s+", " ", unescaped).strip()
    return normalized or None


def _coerce_date_literal(value: str) -> str:
    if "T" not in value:
        return value[:10]
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.date().isoformat()


def _escape_where_literal(value: str) -> str:
    return value.replace("'", "''")


def _coerce_json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(decoded, list):
            return decoded
    return []


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        deduped.append(value)
        seen.add(value)
    return deduped


def _extract_location(raw_event: dict[str, Any]) -> dict[str, Any]:
    coordinates = raw_event.get("location_coordinates") or {}
    return {
        "city": _coerce_text(raw_event.get("location_city")),
        "location_name": _coerce_text(raw_event.get("location_name")),
        "latitude": coordinates.get("lat"),
        "longitude": coordinates.get("lon"),
    }


def _extract_timings(raw_event: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    timings = _coerce_json_list(raw_event.get("timings"))
    if timings:
        first = timings[0] or {}
        last = timings[-1] or {}
        timezone = first.get("timezone") or raw_event.get("timezone")
        return (
            first.get("begin") or raw_event.get("firstdate_begin"),
            last.get("end") or last.get("begin") or raw_event.get("lastdate_end") or raw_event.get("lastdate_begin"),
            timezone,
        )
    return (
        raw_event.get("firstdate_begin"),
        raw_event.get("lastdate_end") or raw_event.get("lastdate_begin"),
        raw_event.get("timezone"),
    )


def _extract_category_ids(raw_event: dict[str, Any], category_field: str | None) -> list[str]:
    category_values: list[str] = []

    source_fields = [category_field] if category_field else ["keywords_fr", "category"]
    for field_name in source_fields:
        if not field_name:
            continue
        raw_value = raw_event.get(field_name)
        if isinstance(raw_value, str):
            cleaned = _coerce_text(raw_value)
            if cleaned:
                category_values.append(cleaned)
            continue
        if isinstance(raw_value, list):
            for entry in raw_value:
                if isinstance(entry, dict):
                    candidate = _coerce_text(entry.get("label")) or _coerce_text(entry.get("value")) or _coerce_text(
                        entry.get("uid")
                    )
                else:
                    candidate = _coerce_text(entry)
                if candidate:
                    category_values.append(candidate)

    return _dedupe_preserving_order(category_values)


def build_text_for_embedding(parts: list[str | None]) -> str:
    cleaned = [part.strip() for part in parts if part and part.strip()]
    return "\n\n".join(cleaned)


def build_records_where_clause(
    start_date: str,
    end_date: str | None = None,
    city: str | None = None,
    agenda_uid: str | None = None,
) -> str:
    clauses = [f"firstdate_begin >= date'{_coerce_date_literal(start_date)}'"]
    if end_date:
        clauses.append(f"firstdate_begin <= date'{_coerce_date_literal(end_date)}'")
    if city:
        clauses.append(f"location_city = '{_escape_where_literal(city)}'")
    if agenda_uid:
        clauses.append(f"originagenda_uid = '{_escape_where_literal(agenda_uid)}'")
    return " and ".join(clauses)


def build_records_request_params(
    start_date: str,
    end_date: str | None = None,
    city: str | None = None,
    agenda_uid: str | None = None,
    offset: int = 0,
    page_size: int = 100,
) -> dict[str, Any]:
    return {
        "limit": page_size,
        "offset": offset,
        "lang": "fr",
        "timezone": "Europe/Paris",
        "where": build_records_where_clause(
            start_date=start_date,
            end_date=end_date,
            city=city,
            agenda_uid=agenda_uid,
        ),
    }


@dataclass
class OpenAgendaClient:
    base_url: str = DEFAULT_BASE_URL
    dataset: str = DEFAULT_DATASET
    timeout: int = DEFAULT_TIMEOUT
    session: Any = None

    def __post_init__(self) -> None:
        if self.session is None:
            self.session = requests.Session()

    @property
    def records_url(self) -> str:
        return f"{self.base_url}/catalog/datasets/{self.dataset}/records"

    def search_agendas(self, search: str, size: int = 10) -> list[dict[str, Any]]:
        normalized_search = _normalize_text(search) or ""
        matches: dict[str, dict[str, Any]] = {}
        offset = 0
        page_size = min(max(size * 10, 100), 100)

        while len(matches) < size:
            response = self.session.get(
                self.records_url,
                params={
                    "limit": page_size,
                    "offset": offset,
                    "lang": "fr",
                    "order_by": "-updatedat",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            records = payload.get("results")
            if not isinstance(records, list) or not records:
                break

            for record in records:
                agenda_uid = _coerce_text(record.get("originagenda_uid"))
                agenda_title = _coerce_text(record.get("originagenda_title"))
                if not agenda_uid or not agenda_title:
                    continue
                searchable_values = [
                    agenda_title,
                    _coerce_text(record.get("title_fr")),
                    _coerce_text(record.get("location_city")),
                ]
                if normalized_search and not any(
                    normalized_search in (_normalize_text(value) or "") for value in searchable_values if value
                ):
                    continue
                matches.setdefault(
                    agenda_uid,
                    {
                        "uid": agenda_uid,
                        "title": agenda_title,
                        "description": None,
                        "official": None,
                        "canonicalUrl": record.get("canonicalurl"),
                    },
                )

            if len(records) < page_size:
                break
            offset += page_size

        return list(matches.values())[:size]

    def fetch_events(
        self,
        agenda_uid: str | None,
        start_date: str,
        end_date: str | None = None,
        city: str | None = None,
        category_field: str | None = None,
        category_ids: list[str] | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        del category_field
        del category_ids

        events: list[dict[str, Any]] = []
        offset = 0
        total_count = None

        while True:
            params = build_records_request_params(
                start_date=start_date,
                end_date=end_date,
                city=city,
                agenda_uid=agenda_uid,
                offset=offset,
                page_size=page_size,
            )
            response = self.session.get(
                self.records_url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            page_events = payload.get("results")
            if not isinstance(page_events, list) or not page_events:
                break

            events.extend(page_events)
            total_count = payload.get("total_count")
            offset += page_size
            if len(page_events) < page_size:
                break
            if isinstance(total_count, int) and offset >= total_count:
                break

        return events


def normalize_event(raw_event: dict[str, Any], agenda_uid: str | None = None, category_field: str | None = None) -> dict[str, Any]:
    title = _strip_html(_coerce_text(raw_event.get("title_fr") or raw_event.get("title")))
    summary = _strip_html(
        _coerce_text(raw_event.get("description_fr") or raw_event.get("description") or raw_event.get("summary"))
    )
    long_description = _strip_html(_coerce_text(raw_event.get("longdescription_fr") or raw_event.get("longDescription")))
    conditions = _strip_html(_coerce_text(raw_event.get("conditions_fr")))
    location = _extract_location(raw_event)
    first_timing, last_timing, timezone = _extract_timings(raw_event)
    categories = _extract_category_ids(raw_event, category_field)

    normalized = {
        "event_uid": _coerce_text(raw_event.get("uid")),
        "agenda_uid": agenda_uid or _coerce_text(raw_event.get("originagenda_uid")),
        "title": title,
        "summary": summary,
        "long_description": long_description,
        "text_for_embedding": build_text_for_embedding(
            [
                title,
                summary,
                long_description,
                conditions,
                location["location_name"],
                location["city"],
                _strip_html(_coerce_text(raw_event.get("originagenda_title"))),
                " ".join(categories) if categories else None,
            ]
        ),
        "city": location["city"],
        "location_name": location["location_name"],
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "first_timing": first_timing,
        "last_timing": last_timing,
        "timezone": timezone,
        "canonical_url": raw_event.get("canonicalurl") or raw_event.get("canonicalUrl") or raw_event.get("url"),
        "categories": categories,
        "source_updated_at": raw_event.get("updatedat") or raw_event.get("updatedAt") or raw_event.get("createdAt"),
        "raw_event": raw_event,
    }

    return {column: normalized.get(column) for column in NORMALIZED_COLUMNS}


def prepare_events_dataset(
    raw_events: list[dict[str, Any]],
    agenda_uid: str | None = None,
    city: str | None = None,
    category_field: str | None = None,
    category_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    normalized_city = _normalize_text(city)
    required_categories = {str(value) for value in (category_ids or [])}
    seen_event_uids: set[str] = set()
    rows: list[dict[str, Any]] = []

    for raw_event in raw_events:
        normalized = normalize_event(raw_event, agenda_uid=agenda_uid, category_field=category_field)
        event_uid = normalized.get("event_uid")
        if not event_uid or event_uid in seen_event_uids:
            continue

        if normalized_city and _normalize_text(normalized.get("city")) != normalized_city:
            continue
        if required_categories and not required_categories.intersection(normalized.get("categories") or []):
            continue

        seen_event_uids.add(event_uid)
        rows.append(normalized)

    return rows
