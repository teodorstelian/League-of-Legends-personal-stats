# Rift Journal

A local FastAPI dashboard for **Bagabondu#1909 · EUNE**, with champion mastery, the ten most recent matches, and recent performance totals. No database or frontend build step required.

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

- Account and match requests use Europe routing; mastery and summoner requests use EUN1.
- Dashboard responses are cached in memory for two minutes. Champion metadata is cached for six hours and uses the latest Data Dragon version.
- Match requests run sequentially to limit bursts. Rate limits, expired keys, missing players, and timeouts produce readable messages. Partial match results show a warning.
- Win rate and averages describe only the loaded recent matches, across all queues, not the full ranked season. No sample stats are presented as live data.
- Champion filtering is case insensitive. The initial view shows the top eight champions, with an option to show all.
- Ranked overview shows current Solo/Duo and Flex tier, division, LP, wins, losses, and win rate. Missing entries appear as Unranked; API failures appear as unavailable.
- The queue selector fetches the latest ten matches for All queues, Solo/Duo, Flex, or ARAM from Riot. Recent win rate and average K/D/A follow that selection; mastery and current standings remain account-wide. Each queue has its own two-minute cache.
- This version is a single-user local app. Keep it bound to localhost.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests mock Riot responses and do not require a real key.

API reference: https://developer.riotgames.com/apis/ · Routing and assets: https://developer.riotgames.com/docs/lol
