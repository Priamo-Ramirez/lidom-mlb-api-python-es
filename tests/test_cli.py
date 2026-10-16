from __future__ import annotations

import json

import pytest

from lidom_mlb_api import LidomGameSummary, LidomScheduleDay, LidomTeamSummary
from lidom_mlb_api.cli import main


def test_cli_today_json_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class FakeApi:
        def get_schedule(self, date_iso: str) -> dict:
            return {"fake": "payload"}

        def parse_schedule_day(self, payload: dict) -> LidomScheduleDay:
            return LidomScheduleDay(
                date="2026-10-16",
                total_games=1,
                games=[
                    LidomGameSummary(
                        game_pk=851509,
                        official_date="2026-10-16",
                        game_date_utc="2026-10-16T23:00:00Z",
                        away_team="Aguilas Cibaenas",
                        home_team="Gigantes del Cibao",
                        status="Scheduled",
                        venue="Estadio Julian Javier",
                    )
                ],
            )

    monkeypatch.setattr("lidom_mlb_api.cli.LidomStatsApi", lambda: FakeApi())
    monkeypatch.setattr("lidom_mlb_api.cli.get_today_in_dominican_republic", lambda: "2026-10-16")
    monkeypatch.setattr("sys.argv", ["lidom-api", "today", "--json"])

    main()
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert payload["date"] == "2026-10-16"
    assert payload["total_games"] == 1
    assert payload["games"][0]["home_team"] == "Gigantes del Cibao"


def test_cli_teams_plain_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    class FakeApi:
        def get_teams(self, season: int | None = None) -> dict:
            return {"season": season}

        def parse_teams(self, payload: dict) -> list[LidomTeamSummary]:
            return [
                LidomTeamSummary(
                    team_id=672,
                    name="Tigres del Licey",
                    venue="Estadio Quisqueya Juan Marichal",
                )
            ]

    monkeypatch.setattr("lidom_mlb_api.cli.LidomStatsApi", lambda: FakeApi())
    monkeypatch.setattr("sys.argv", ["lidom-api", "teams", "--season", "2026"])

    main()
    output = capsys.readouterr().out

    assert "Equipos LIDOM (1):" in output
    assert "Tigres del Licey" in output
