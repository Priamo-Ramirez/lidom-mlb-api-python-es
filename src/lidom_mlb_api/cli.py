"""CLI para consultar LIDOM desde MLB Stats API."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .client import LidomScheduleDay, LidomStatsApi, get_today_in_dominican_republic


def _print_schedule(schedule_day: LidomScheduleDay) -> None:
    if not schedule_day.games:
        print(f"Sin juegos para la fecha {schedule_day.date or 'indicada'}.")
        return

    print(f"Calendario de LIDOM para {schedule_day.date} ({schedule_day.total_games} juegos)")
    for game in schedule_day.games:
        print(
            f"- {game.away_team} @ {game.home_team} | "
            f"{game.status} | {game.venue} | gamePk={game.game_pk}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI para consultar LIDOM en MLB Stats API")
    subparsers = parser.add_subparsers(dest="command", required=True)

    games_parser = subparsers.add_parser("games", help="Consultar juegos por fecha (YYYY-MM-DD)")
    games_parser.add_argument("--date", required=True, help="Fecha en formato YYYY-MM-DD")
    games_parser.add_argument("--json", action="store_true", help="Imprimir salida JSON")

    today_parser = subparsers.add_parser("today", help="Consultar juegos de hoy en hora RD")
    today_parser.add_argument("--json", action="store_true", help="Imprimir salida JSON")

    teams_parser = subparsers.add_parser("teams", help="Listar equipos LIDOM")
    teams_parser.add_argument("--season", type=int, help="Temporada, por ejemplo 2026")
    teams_parser.add_argument("--json", action="store_true", help="Imprimir salida JSON")

    args = parser.parse_args()
    api = LidomStatsApi()

    if args.command == "games":
        payload = api.get_schedule(args.date)
        schedule_day = api.parse_schedule_day(payload)
        if args.json:
            print(json.dumps(asdict(schedule_day), indent=2, ensure_ascii=False))
            return
        _print_schedule(schedule_day)
        return

    if args.command == "today":
        today = get_today_in_dominican_republic()
        payload = api.get_schedule(today)
        schedule_day = api.parse_schedule_day(payload)
        if args.json:
            print(json.dumps(asdict(schedule_day), indent=2, ensure_ascii=False))
            return
        _print_schedule(schedule_day)
        return

    payload = api.get_teams(season=args.season)
    teams = api.parse_teams(payload)
    if args.json:
        print(json.dumps([asdict(team) for team in teams], indent=2, ensure_ascii=False))
        return

    print(f"Equipos LIDOM ({len(teams)}):")
    for team in teams:
        print(f"- {team.name} | id={team.team_id} | estadio={team.venue}")
