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
- Dashboard and champion stats use all imported games for the chosen queue, not lifetime totals. Queue options are All, Solo/Duo and Flex. Profile/mastery/ranks refresh in the background every five minutes, and persisted data serves immediately after the initial setup.
- Pages poll sync status and refresh saved stats as imports progress. Search and Browse all cover all champions, including unplayed champions.
- Account and match requests use Europe routing; mastery and summoner requests use EUN1. Champion assets use the latest Data Dragon catalog cached for six hours.
- This version is a single-user local app. Keep it bound to localhost.

## Match analysis and Rift Score v1

Top navigation links to Overview, Champions, Matches, and Lanes. `/champions` lists the full champion catalog with queue-aware scores, sample sizes, win rate, W/L, average K/D/A, and mastery. Search by name, filter played champions or minimum scored games, and sort by score (both directions), games, win rate, mastery, or name. Unscored champions sort last for either score direction. The directory refreshes every 30 seconds while visible; champion links open individual journals.

The dashboard and champion pages show average Rift Score and lane averages for the selected queue. Champion cards show each champion's average and scored/saved sample counts. Averages give every scored match equal weight, include valid zero scores, and exclude unscored/remake/unsupported matches. Fewer than five scored games is labeled as a small sample. Top, Jungle, Mid, Bot, and Support use Riot's team position; ARAM and unknown positions are separate groups. Averages update as details finish syncing. Scores across modes and roles have different comparisons and should be interpreted with the sample and queue in mind.

Click any saved match to open both team scoreboards and inspect each player's final items, spells, runes, damage, economy, vision, objective pressure, healing, shielding, CC, and time dead. Full match responses are saved locally. The worker fills in details for previously saved summaries; opening a match can fetch missing details immediately. Item/spell/rune labels use the match's patch where Data Dragon provides it; unknown assets fall back to IDs with a warning.

Rift Score is a custom within-match heuristic from 0 to 100. Classic weights: champion damage 20%, kill participation 20%, survival 15%, gold 15%, vision 15%, objective damage 15%. For supports, damage impact includes ally healing and shielding. Each component compares the player to the opposing player in the same Riot-assigned role; when a unique same-role opponent is unavailable, it uses the opposing team's average. ARAM uses the team average and excludes vision/objectives.

For each metric: `100 * own / (own + comparison)`, inverted for deaths; both zero gives 50. Available component weights are normalized to sum to 100. Missing metrics are omitted. Short games under three minutes, early-surrender/remake flags, and unsupported game modes are not scored. Winning adds no bonus. A score of 50 means equal measured contributions to the comparison, not a population average, official Riot grade, or rank estimate. Positioning, matchup difficulty, and unrecorded utility are not measured. The formula and component values are visible on each match page.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/run
```

Tests mock Riot responses and do not require a real key.

API reference: https://developer.riotgames.com/apis/ · Routing and assets: https://developer.riotgames.com/docs/lol

History policy: only Ranked Solo/Duo (420) and Ranked Flex (440) matches lasting at least 180 seconds are stored. Early-surrender/remake flags are also excluded. Startup removes previously saved non-ranked games/remakes and resets the historical cursor once for ranked-only pagination; the existing import target is retained. Riot match-list queries use type=ranked; the storage boundary independently enforces queue and duration.
