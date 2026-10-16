# Guía de MLB Stats API (Liga Dominicana de Béisbol / LIDOM)

Documentación y ejemplos con enfoque en **Python** para consultar datos de **LIDOM** en la MLB Stats API pública.

## ¿Está disponible LIDOM en la API?

Sí. LIDOM está disponible en la MLB Stats API.

- Deporte Winter Leagues: `sportId=17`
- Liga Dominicana (LIDOM): `leagueId=131`

La consulta principal del calendario es:

```text
GET /api/v1/schedule?sportId=17&leagueId=131&date=YYYY-MM-DD
```

> Importante: `schedule` exige `sportId` (o `gamePk`). Solo `leagueId` no funciona.

---

## Mapa rápido de endpoints para LIDOM

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

## Notas y consideraciones

- Algunos campos de metadatos en live feeds de winter leagues pueden venir como `null` (por ejemplo, campos de liga/deporte en ciertos payloads de `gameData`), así que conviene parsear de forma defensiva.
- Al inicio de temporada, `standings` puede devolver registros vacíos aunque ya exista calendario.
- Los estados del juego (`Scheduled`, `Pre-Game`, `In Progress`, `Final`) están en `status.detailedState`.

---

## Próximas mejoras recomendadas (Python)

Si luego lo conviertes en una integración más grande:

1. Agregar reintentos y backoff para errores de red.
2. Implementar caché de respuestas de calendario por fecha.
3. Normalizar equipos/estadios en modelos tipados (Pydantic/dataclasses).
4. Agregar argumentos de CLI (`--date`, `--season`, `--json`) para automatización.
5. Añadir tests con fixtures JSON guardados para estabilidad.
