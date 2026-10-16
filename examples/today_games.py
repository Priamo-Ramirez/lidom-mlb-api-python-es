"""Ejemplo: imprimir los juegos de hoy de LIDOM usando MLB Stats API."""

from lidom_mlb_api import LidomStatsApi, get_today_in_dominican_republic


def main() -> None:
    api = LidomStatsApi()
    today = get_today_in_dominican_republic()
    schedule = api.get_schedule(today)
    games = api.summarize_games(schedule)

    print(f"Calendario de LIDOM para {today}")
    if not games:
        print("No se devolvieron juegos para esta fecha.")
        return

    for game in games:
        print(
            f"- {game.away_team} @ {game.home_team} | "
            f"{game.status} | {game.venue} | gamePk={game.game_pk}"
        )


if __name__ == "__main__":
    main()
