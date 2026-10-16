"""Cliente mínimo de Python para MLB Stats API con utilidades para LIDOM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo
import json

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


def get_today_in_dominican_republic() -> str:
    """Devuelve la fecha de hoy en zona horaria de RD (YYYY-MM-DD)."""
    return datetime.now(ZoneInfo(DOMINICAN_TZ)).strftime("%Y-%m-%d")


class LidomStatsApi:
    """Ayudante simple para endpoints públicos de MLB Stats API usados por LIDOM."""

    def __init__(self, base_url: str = BASE_URL, timeout_seconds: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = f"?{urlencode(params)}" if params else ""
        url = f"{self.base_url}{path}{query}"
        with urlopen(url, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

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
