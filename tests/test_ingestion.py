from openagenda_rag.ingestion import (
    OpenAgendaClient,
    build_records_request_params,
    build_records_where_clause,
    prepare_events_dataset,
)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class RecordingSession:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": dict(params or {}), "timeout": timeout})
        payload = self.payloads.pop(0)
        return FakeResponse(payload)


EXPECTED_KEYS = [
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


def test_fetch_events_paginates_until_total_count_is_reached():
    session = RecordingSession(
        [
            {
                "total_count": 3,
                "results": [
                    {"uid": "evt-1", "title_fr": "Concert 1"},
                    {"uid": "evt-2", "title_fr": "Concert 2"},
                ],
            },
            {
                "total_count": 3,
                "results": [
                    {"uid": "evt-3", "title_fr": "Concert 3"},
                ],
            },
        ]
    )
    client = OpenAgendaClient(session=session)

    events = client.fetch_events(
        agenda_uid="agenda-123",
        city="Paris",
        start_date="2025-01-01",
        end_date="2025-12-31",
        page_size=2,
    )

    assert [event["uid"] for event in events] == ["evt-1", "evt-2", "evt-3"]
    assert [call["params"]["offset"] for call in session.calls] == [0, 2]
    assert session.calls[0]["params"]["where"] == (
        "firstdate_begin >= date'2025-01-01' and "
        "firstdate_begin <= date'2025-12-31' and "
        "location_city = 'Paris' and "
        "originagenda_uid = 'agenda-123'"
    )


def test_build_records_where_clause_escapes_strings_and_dates():
    where_clause = build_records_where_clause(
        start_date="2025-01-01T08:30:00+01:00",
        end_date="2025-12-31",
        city="L'Haÿ-les-Roses",
        agenda_uid="agenda'42",
    )

    assert where_clause == (
        "firstdate_begin >= date'2025-01-01' and "
        "firstdate_begin <= date'2025-12-31' and "
        "location_city = 'L''Haÿ-les-Roses' and "
        "originagenda_uid = 'agenda''42'"
    )


def test_build_records_request_params_uses_public_dataset_defaults():
    params = build_records_request_params(
        start_date="2025-01-01",
        end_date="2025-12-31",
        city="Paris",
        agenda_uid="979472",
        offset=200,
        page_size=100,
    )

    assert params == {
        "limit": 100,
        "offset": 200,
        "lang": "fr",
        "timezone": "Europe/Paris",
        "where": (
            "firstdate_begin >= date'2025-01-01' and "
            "firstdate_begin <= date'2025-12-31' and "
            "location_city = 'Paris' and "
            "originagenda_uid = '979472'"
        ),
    }


def test_build_records_request_params_caps_page_size_to_dataset_limit():
    params = build_records_request_params(
        start_date="2025-01-01",
        offset=0,
        page_size=500,
    )

    assert params["limit"] == 100


def test_prepare_events_dataset_normalizes_incomplete_records():
    raw_events = [
        {
            "uid": "evt-1",
            "title_fr": "Atelier numerique",
            "description_fr": "Initiation a Python",
            "longdescription_fr": None,
            "timings": None,
            "updatedat": "2025-03-18T10:00:00Z",
            "originagenda_uid": "agenda-123",
        }
    ]

    rows = prepare_events_dataset(raw_events)

    assert len(rows) == 1
    row = rows[0]
    assert list(row.keys()) == EXPECTED_KEYS
    assert row["agenda_uid"] == "agenda-123"
    assert row["city"] is None
    assert row["location_name"] is None
    assert row["categories"] == []
    assert row["latitude"] is None
    assert row["longitude"] is None
    assert row["first_timing"] is None
    assert row["last_timing"] is None
    assert "Atelier numerique" in row["text_for_embedding"]
    assert "Initiation a Python" in row["text_for_embedding"]


def test_prepare_events_dataset_strips_html_and_parses_coordinates():
    raw_events = [
        {
            "uid": "evt-1",
            "originagenda_uid": "agenda-123",
            "title_fr": "Concert",
            "description_fr": "<p>Une <strong>belle</strong> soiree</p>",
            "longdescription_fr": "<div>Avec <em>invites</em></div>",
            "conditions_fr": "Reservation conseillee",
            "keywords_fr": ["Musique", "Live"],
            "location_name": "Salle des fetes",
            "location_city": "Paris",
            "location_coordinates": {"lat": 48.85, "lon": 2.35},
            "timings": (
                '[{"begin": "2025-06-01T10:00:00+02:00", "end": "2025-06-01T12:00:00+02:00"}, '
                '{"begin": "2025-06-02T10:00:00+02:00", "end": "2025-06-02T12:00:00+02:00"}]'
            ),
            "canonicalurl": "https://example.test/event",
            "updatedat": "2025-05-01T10:00:00Z",
        }
    ]

    rows = prepare_events_dataset(raw_events)

    assert len(rows) == 1
    row = rows[0]
    assert row["summary"] == "Une belle soiree"
    assert row["long_description"] == "Avec invites"
    assert row["latitude"] == 48.85
    assert row["longitude"] == 2.35
    assert row["first_timing"] == "2025-06-01T10:00:00+02:00"
    assert row["last_timing"] == "2025-06-02T12:00:00+02:00"
    assert row["canonical_url"] == "https://example.test/event"
    assert row["categories"] == ["Musique", "Live"]
    assert "Reservation conseillee" in row["text_for_embedding"]


def test_prepare_events_dataset_filters_by_city_and_deduplicates_on_event_uid():
    raw_events = [
        {
            "uid": "evt-1",
            "originagenda_uid": "agenda-123",
            "title_fr": "Concert",
            "location_city": "Paris",
            "location_name": "Salle des fetes",
            "firstdate_begin": "2025-06-01T10:00:00+02:00",
            "lastdate_end": "2025-06-01T12:00:00+02:00",
        },
        {
            "uid": "evt-1",
            "originagenda_uid": "agenda-123",
            "title_fr": "Concert duplicate",
            "location_city": "Paris",
            "location_name": "Salle des fetes",
            "firstdate_begin": "2025-06-01T10:00:00+02:00",
            "lastdate_end": "2025-06-01T12:00:00+02:00",
        },
        {
            "uid": "evt-2",
            "originagenda_uid": "agenda-123",
            "title_fr": "Expo",
            "location_city": "Lyon",
            "location_name": "Musee",
            "firstdate_begin": "2025-06-02T10:00:00+02:00",
            "lastdate_end": "2025-06-02T12:00:00+02:00",
        },
    ]

    rows = prepare_events_dataset(raw_events, city="paris")

    assert len(rows) == 1
    assert rows[0]["event_uid"] == "evt-1"
    assert rows[0]["city"] == "Paris"


def test_prepare_events_dataset_filters_by_category_when_requested():
    raw_events = [
        {
            "uid": "evt-1",
            "originagenda_uid": "agenda-123",
            "title_fr": "Concert",
            "keywords_fr": ["music", "family"],
            "firstdate_begin": "2025-06-01T10:00:00+02:00",
            "lastdate_end": "2025-06-01T12:00:00+02:00",
        },
        {
            "uid": "evt-2",
            "originagenda_uid": "agenda-123",
            "title_fr": "Atelier",
            "keywords_fr": ["workshop"],
            "firstdate_begin": "2025-06-01T10:00:00+02:00",
            "lastdate_end": "2025-06-01T12:00:00+02:00",
        },
    ]

    rows = prepare_events_dataset(
        raw_events,
        category_field="keywords_fr",
        category_ids=["music"],
    )

    assert [row["event_uid"] for row in rows] == ["evt-1"]
    assert rows[0]["categories"] == ["music", "family"]
