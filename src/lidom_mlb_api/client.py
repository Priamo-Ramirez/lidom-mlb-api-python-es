"""Cliente de Python para MLB Stats API con utilidades para LIDOM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo
import json
import time

BASE_URL = "https://statsapi.mlb.com/api/v1"
WINTER_LEAGUES_SPORT_ID = 17
LIDOM_LEAGUE_ID = 131
DOMINICAN_TZ = "America/Santo_Domingo"


@dataclass(frozen=True)
class LidomGameSummary:
    """Estructura amigable para mostrar listados básicos de juegos."""

    game_pk: int
    official_date: str
    game_date_utc: str
    away_team: str
    home_team: str
    status: str
    venue: str


@dataclass(frozen=True)
class LidomTeamSummary:
    """Modelo tipado para datos de equipo en LIDOM."""

    team_id: int
    name: str
    venue: str


@dataclass(frozen=True)
class LidomScheduleDay:
    """Modelo tipado para un día de calendario de LIDOM."""

    date: str
    total_games: int
    games: list[LidomGameSummary]


def get_today_in_dominican_republic() -> str:
    """Devuelve la fecha de hoy en zona horaria de RD (YYYY-MM-DD)."""
    return datetime.now(ZoneInfo(DOMINICAN_TZ)).strftime("%Y-%m-%d")


class LidomStatsApi:
    """Ayudante para endpoints públicos de MLB Stats API usados por LIDOM."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout_seconds: int = 20,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = f"?{urlencode(params)}" if params else ""
        url = f"{self.base_url}{path}{query}"
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                with urlopen(url, timeout=self.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                last_error = error
                should_retry = error.code in {429, 500, 502, 503, 504}
                if not should_retry or attempt >= self.max_retries:
                    raise
            except URLError as error:
                last_error = error
                if attempt >= self.max_retries:
                    raise

            sleep_seconds = self.backoff_seconds * (2**attempt)
            time.sleep(sleep_seconds)

        if last_error is not None:
            raise last_error
        raise RuntimeError("No se pudo completar la solicitud a MLB Stats API.")

    def get_sports(self) -> dict[str, Any]:
        return self._get_json("/sports")

    def get_winter_leagues(self) -> dict[str, Any]:
        return self._get_json("/leagues", params={"sportId": WINTER_LEAGUES_SPORT_ID})

    def get_lidom_league(self) -> dict[str, Any] | None:
        data = self.get_winter_leagues()
        for league in data.get("leagues", []):
            if league.get("id") == LIDOM_LEAGUE_ID or league.get("abbreviation") == "LIDOM":
                return league
        return None

    def get_schedule(self, date_iso: str) -> dict[str, Any]:
        return self._get_json(
            "/schedule",
            params={
                "sportId": WINTER_LEAGUES_SPORT_ID,
                "leagueId": LIDOM_LEAGUE_ID,
                "date": date_iso,
            },
        )

    def get_today_schedule(self) -> dict[str, Any]:
        return self.get_schedule(get_today_in_dominican_republic())

    def get_teams(self, season: int | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {
            "sportId": WINTER_LEAGUES_SPORT_ID,
            "leagueIds": LIDOM_LEAGUE_ID,
        }
        if season is not None:
            params["season"] = season
        return self._get_json("/teams", params=params)

    def get_game_live_feed(self, game_pk: int) -> dict[str, Any]:
        return self._get_json(f".1/game/{game_pk}/feed/live")

    @staticmethod
    def summarize_games(schedule_payload: dict[str, Any]) -> list[LidomGameSummary]:
        dates = schedule_payload.get("dates", [])
        if not dates:
            return []

        summaries: list[LidomGameSummary] = []
        for game in dates[0].get("games", []):
            summaries.append(
                LidomGameSummary(
                    game_pk=game["gamePk"],
                    official_date=game.get("officialDate", ""),
                    game_date_utc=game.get("gameDate", ""),
                    away_team=game.get("teams", {}).get("away", {}).get("team", {}).get("name", ""),
                    home_team=game.get("teams", {}).get("home", {}).get("team", {}).get("name", ""),
                    status=game.get("status", {}).get("detailedState", ""),
                    venue=game.get("venue", {}).get("name", ""),
                )
            )
        return summaries

    @staticmethod
    def parse_schedule_day(schedule_payload: dict[str, Any]) -> LidomScheduleDay:
        """Convierte el payload de schedule a un modelo tipado."""
        dates = schedule_payload.get("dates", [])
        if not dates:
            return LidomScheduleDay(date="", total_games=0, games=[])

        day_data = dates[0]
        games = LidomStatsApi.summarize_games(schedule_payload)
        return LidomScheduleDay(
            date=day_data.get("date", ""),
            total_games=day_data.get("totalGames", 0),
            games=games,
        )

    @staticmethod
    def parse_teams(teams_payload: dict[str, Any]) -> list[LidomTeamSummary]:
        """Convierte el payload de teams a una lista tipada de equipos."""
        teams: list[LidomTeamSummary] = []
        for item in teams_payload.get("teams", []):
            teams.append(
                LidomTeamSummary(
                    team_id=item.get("id", 0),
                    name=item.get("name", ""),
                    venue=item.get("venue", {}).get("name", ""),
                )
            )
        return teams
