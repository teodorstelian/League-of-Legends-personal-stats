# Rift Journal

A local FastAPI dashboard for **Bagabondu#1909 · EUNE**, with champion mastery, saved match history, and performance totals. SQLite is created automatically; no frontend build step required.

## Run on Windows

Install Python 3.11 or newer, then run from this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000.

The local `.env` file is already created and ignored by Git. Put your key after the equals sign:

```dotenv
RIOT_API_KEY=your-key-here
RIOT_ID=Bagabondu#1909
```

On a fresh clone, copy `.env.example` to `.env` first. The key is only sent from the server to Riot in the `X-Riot-Token` header. Never add it to frontend files. Updating `.env` takes effect on the next refresh without restarting the server. An explicitly configured `.env` value overrides the corresponding process environment variable.

## Behavior

- A background worker starts with the app and imports a target of 100 recent matches in batches of 20. Import 100 more extends the target; a batch may slightly exceed the target.
- SQLite lives in `data/journal.sqlite3`, ignored by Git. Matches are deduplicated per Riot ID and match ID. The import position, target, pause state, and player profile survive restarts. Keys are never stored in the database.
- The worker checks for new games every five minutes while running. Close the server and syncing stops; restart it to resume. Run only one server worker against this database.
- Pause/resume and import-more controls appear on both pages, along with saved count, target, oldest saved game, and status. An in-flight request may finish after pausing.
- Historical pagination uses a fixed end timestamp. Exhausting Riot's available history stops older imports; newer games are still checked automatically.
- Riot requests share a conservative 1.3-second spacing. On a 429 response the worker honors Retry-After and retries later; network/key failures also retry without losing saved matches.
- Dashboard and champion stats use all imported games for the chosen queue, not lifetime totals. Queue options are All, Solo/Duo, Flex, and ARAM. Profile/mastery/ranks refresh in the background every five minutes, and persisted data serves immediately after the initial setup.
- Pages poll sync status and refresh saved stats as imports progress. Search and Browse all cover all champions, including unplayed champions.
- Account and match requests use Europe routing; mastery and summoner requests use EUN1. Champion assets use the latest Data Dragon catalog cached for six hours.
- This version is a single-user local app. Keep it bound to localhost.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/run
```

Tests mock Riot responses and do not require a real key.

API reference: https://developer.riotgames.com/apis/ · Routing and assets: https://developer.riotgames.com/docs/lol
