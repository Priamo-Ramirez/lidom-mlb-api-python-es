# Guía de MLB Stats API (Liga Dominicana de Béisbol / LIDOM)

[![CI](https://github.com/Priamo-Ramirez/lidom-mlb-api-python-es/actions/workflows/ci.yml/badge.svg)](https://github.com/Priamo-Ramirez/lidom-mlb-api-python-es/actions/workflows/ci.yml)

Referencia técnica y ejemplos en **Python** para consultar **LIDOM** en la MLB Stats API pública.

## Identificadores de LIDOM en la API

- Deporte Winter Leagues: `sportId=17`
- Liga Dominicana (LIDOM): `leagueId=131`

La consulta principal del calendario es:

```text
GET /api/v1/schedule?sportId=17&leagueId=131&date=YYYY-MM-DD
```

> Importante: `schedule` exige `sportId` (o `gamePk`). Solo `leagueId` no funciona.

---

## Referencia de endpoints para LIDOM

URL base:

```text
https://statsapi.mlb.com/api/v1
```

### 1) Descubrir deportes

```bash
curl -s "https://statsapi.mlb.com/api/v1/sports"
```

Buscar:
- `id: 17`
- `name: "Winter Leagues"`

### 2) Descubrir ligas de invierno (incluye LIDOM)

```bash
curl -s "https://statsapi.mlb.com/api/v1/leagues?sportId=17"
```

Buscar:
- `id: 131`
- `name: "Liga de Beisbol Dominicano"`
- `abbreviation: "LIDOM"`

### 3) Consultar juegos de LIDOM por fecha

```bash
curl -s "https://statsapi.mlb.com/api/v1/schedule?sportId=17&leagueId=131&date=2026-10-16"
```

Campos útiles de la respuesta:
- `totalGames`
- `dates[0].games[].gamePk`
- `dates[0].games[].teams.away.team.name`
- `dates[0].games[].teams.home.team.name`
- `dates[0].games[].status.detailedState`
- `dates[0].games[].gameDate`

### 4) Listado de equipos LIDOM

```bash
curl -s "https://statsapi.mlb.com/api/v1/teams?sportId=17&leagueIds=131&season=2026"
```

### 5) Feed en vivo de un juego específico

Usa el `gamePk` obtenido desde `schedule`:

```bash
curl -s "https://statsapi.mlb.com/api/v1.1/game/<gamePk>/feed/live"
```

---

## Uso en Python (este repositorio)

## Estructura

- `src/lidom_mlb_api/client.py` — cliente reutilizable de la API
- `src/lidom_mlb_api/cli.py` — CLI (`lidom-api`) para consultar juegos y equipos
- `examples/today_games.py` — ejemplo ejecutable para imprimir los juegos de hoy en LIDOM

## Ejecutar ejemplo

Desde la raíz del repositorio:

```bash
PYTHONPATH=src python3 examples/today_games.py
```

Salida esperada (formato):

```text
Calendario de LIDOM para 2026-10-16
- Aguilas Cibaenas @ Gigantes del Cibao | Scheduled | Estadio Julian Javier | gamePk=851509
- Tigres del Licey @ Leones del Escogido | Scheduled | Estadio Quisqueya Juan Marichal | gamePk=851491
- Estrellas Orientales @ Toros del Este | Pre-Game | Estadio Francisco Micheli | gamePk=851435
```

## Snippet mínimo en Python

```python
from lidom_mlb_api import LidomStatsApi, get_today_in_dominican_republic

api = LidomStatsApi()
today = get_today_in_dominican_republic()  # Fecha en zona America/Santo_Domingo
schedule = api.get_schedule(today)
games = api.summarize_games(schedule)

for game in games:
    print(game.away_team, "@", game.home_team, game.status, game.game_pk)
```

---

## CLI

Después de instalar el paquete en tu entorno (`pip install -e .`), puedes usar:

```bash
lidom-api today
lidom-api games --date 2026-10-16
lidom-api teams --season 2026
```

Salida en JSON:

```bash
lidom-api today --json
lidom-api teams --season 2026 --json
```

También puedes ejecutarlo como módulo:

```bash
PYTHONPATH=src python3 -m lidom_mlb_api today
```

---

## Modelos tipados

El cliente ya incluye modelos dataclass para estructurar datos:

- `LidomGameSummary`
- `LidomScheduleDay`
- `LidomTeamSummary`

Helpers de parseo:

- `parse_schedule_day(payload)` → `LidomScheduleDay`
- `parse_teams(payload)` → `list[LidomTeamSummary]`

---

## Configuración de reintentos y backoff

`LidomStatsApi` aplica reintentos automáticos con backoff exponencial para errores transitorios.

Defaults:
- `max_retries=3`
- `backoff_seconds=1.0`
- Reintenta en `429`, `500`, `502`, `503`, `504`, y errores de red (`URLError`).

Configuración del cliente:

```python
api = LidomStatsApi(max_retries=5, backoff_seconds=0.5, timeout_seconds=20)
```

---

## Pruebas con fixtures

El proyecto incluye pruebas con `pytest` y fixtures JSON en `tests/fixtures/` para:

- parseo de calendario con juegos y sin juegos,
- parseo de equipos,
- reintentos de red con backoff,
- salida del CLI en modo JSON y texto.

Ejecutar tests localmente:

```bash
python3 -m pip install -e ".[test]"
pytest -q
```

---

## CI (GitHub Actions)

Se incluye workflow en `.github/workflows/ci.yml` que ejecuta los tests en:

- Python 3.10
- Python 3.11
- Python 3.12

Además, el workflow ejecuta lint con Ruff antes de correr los tests:

```bash
ruff check .
```

---

## Pre-commit

Instalación:

```bash
python3 -m pip install -e ".[test]"
pre-commit install
pre-commit install --hook-type commit-msg
```

Ejecución manual sobre todo el repo:

```bash
pre-commit run --all-files
```

Hooks incluidos:

- `ruff-check`
- `pytest -q`
- `conventional-commit-msg` (etapa `commit-msg`)

Formato esperado para commits:

```text
<tipo>(<scope opcional>): <descripción>
```

Tipos permitidos:

```text
feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
```

Ejemplo:

```text
feat(cli): agregar comando today
```

---

## Limitaciones conocidas

- Algunos campos de metadatos en live feeds de winter leagues pueden venir como `null` (por ejemplo, campos de liga/deporte en ciertos payloads de `gameData`), por lo que el parseo debe ser defensivo.
- Al inicio de temporada, `standings` puede devolver registros vacíos aunque ya exista calendario.
- Los estados del juego (`Scheduled`, `Pre-Game`, `In Progress`, `Final`) están en `status.detailedState`.

---
