from __future__ import annotations

import json
from pathlib import Path
from urllib.error import URLError

import pytest

import lidom_mlb_api.client as client_module
from lidom_mlb_api import LidomStatsApi

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def test_parse_schedule_day_with_games() -> None:
    payload = load_fixture("schedule_with_games.json")
    parsed = LidomStatsApi.parse_schedule_day(payload)

    assert parsed.date == "2026-10-16"
    assert parsed.total_games == 2
    assert len(parsed.games) == 2
    assert parsed.games[0].away_team == "Aguilas Cibaenas"
    assert parsed.games[1].status == "Pre-Game"


def test_parse_schedule_day_without_games() -> None:
    payload = load_fixture("schedule_no_games.json")
    parsed = LidomStatsApi.parse_schedule_day(payload)

    assert parsed.date == ""
    assert parsed.total_games == 0
    assert parsed.games == []


def test_parse_teams_payload() -> None:
    payload = load_fixture("teams_2026.json")
    teams = LidomStatsApi.parse_teams(payload)

    assert len(teams) == 2
    assert teams[0].team_id == 672
    assert teams[1].name == "Aguilas Cibaenas"


def test_get_json_retries_and_succeeds_after_transient_error(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = {"count": 0}
    sleep_calls: list[float] = []

    class FakeResponse:
        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def read(self) -> bytes:
            return b'{"ok": true}'

    def fake_urlopen(url: str, timeout: int) -> FakeResponse:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise URLError("temporary network failure")
        return FakeResponse()

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)
    monkeypatch.setattr(client_module.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    api = LidomStatsApi(max_retries=3, backoff_seconds=0.1)
    result = api.get_sports()

    assert result == {"ok": True}
    assert attempts["count"] == 3
    assert sleep_calls == [0.1, 0.2]


def test_get_json_raises_after_retry_exhaustion(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = {"count": 0}
    sleep_calls: list[float] = []

    def failing_urlopen(url: str, timeout: int):
        attempts["count"] += 1
        raise URLError("still failing")

    monkeypatch.setattr(client_module, "urlopen", failing_urlopen)
    monkeypatch.setattr(client_module.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    api = LidomStatsApi(max_retries=2, backoff_seconds=0.5)

    with pytest.raises(URLError):
        api.get_sports()

    assert attempts["count"] == 3
    assert sleep_calls == [0.5, 1.0]
