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
- The worker checks for new games once on startup and when Check new games is clicked. Periodic Riot fetching is disabled. Close the server and syncing stops; restart it to resume. Run only one server worker against this database.
- Pause/resume and import-more controls appear on both pages, along with saved count, target, oldest saved game, and status. An in-flight request may finish after pausing.
- Historical pagination uses a fixed end timestamp. Exhausting Riot's available history stops older imports; newer games are still checked automatically.
- Riot requests share a conservative 1.3-second spacing. On a 429 response the worker honors Retry-After and retries later; network/key failures also retry without losing saved matches.
- Dashboard and champion stats use all imported games for the chosen queue, not lifetime totals. Queue options are All, Solo/Duo and Flex. Profile/mastery/ranks refresh on startup and manual checks, and persisted data serves immediately after the initial setup.
- Pages poll sync status and refresh saved stats as imports progress. Search and Browse all cover all champions, including unplayed champions.
- Account and match requests use Europe routing; mastery and summoner requests use EUN1. Champion assets use the latest Data Dragon catalog cached for six hours.
- This version is a single-user local app. Keep it bound to localhost.

## Match analysis and Rift Score v3

`/trends` shows 12 weekly Rift Score bars, rolling last-30 vs previous-30-day comparisons, and champion form. Queue, role, and champion filters apply throughout. Weeks run Monday–Sunday in UTC; the current week is partial and empty weeks have no score. Select a bar for game/scored counts. Comparisons show score, win rate (percentage-point changes), deaths/game, damage/min, and vision/min with per-metric coverage. Rates divide totals by covered game minutes. Champion form needs three scored games in each period; changes of at least three score points are labeled improving/declining, otherwise steady. These are provisional descriptive labels, not significance tests; imported history may be incomplete. The page refreshes every 30 seconds while visible.

`/tier-list` automatically builds a personal champion tier list for each role from that role's saved ranked games. Queue filters and a minimum scored-game requirement (default three) control eligibility. S starts at 75, A at 60, B at 50, C at 40, and D below 40; thresholds match gauge colors. Champions are sorted by average, then sample size and name within tiers. Under-sampled/unscored picks are listed separately, and unknown-role games are excluded. The page refreshes every 30 seconds while visible. This is a personal performance ranking, not a global meta recommendation.

Top navigation links to Overview, Champions, Matches, and Lanes. `/champions` lists the full champion catalog with queue-aware scores, sample sizes, win rate, W/L, average K/D/A, and mastery. Search by name, filter played champions or minimum scored games, and sort by score (both directions), games, win rate, mastery, or name. Unscored champions sort last for either score direction. The directory refreshes every 30 seconds while visible; champion links open individual journals.

`/matches` is the dedicated saved-history page with queue, champion, and win/loss filters, sorting by date or score, item builds, score gauges, and 25-at-a-time display. Summary statistics use all matching games, not just the visible page. Background sync updates the list while preserving filters. The overview keeps only a five-game preview linking to the full page; match-detail back links return to Matches.

The dashboard and champion pages show average Rift Score and lane averages for the selected queue. Champion cards show each champion's average and scored/saved sample counts. Averages give every scored match equal weight, include valid zero scores, and exclude unscored/remake/unsupported matches. Fewer than five scored games is labeled as a small sample. Top, Jungle, Mid, Bot, and Support use Riot's team position; ARAM and unknown positions are separate groups. Averages update as details finish syncing. Scores across modes and roles have different provisional targets and should be interpreted with the sample and queue in mind.

Click any saved match to open both team scoreboards and inspect each player's final items, spells, runes, damage, economy, vision, objective pressure, healing, shielding, CC, and time dead. Full match responses are saved locally. The worker fills in details for previously saved summaries; opening a match can fetch missing details immediately. Item/spell/rune labels use the match's patch where Data Dragon provides it; unknown assets fall back to IDs with a warning.

Rift Score v3 scores each player independently using provisional role benchmarks defined in `app/scoring.py`. Targets are product choices, not measured population averages. Champion damage, gold, vision, objectives, and deaths are normalized per minute. Kill participation is based on the player's own team. Positive metrics score `min(100, own / target * 100)`; survival scores `max(0, 100 * (1 - deaths_per_minute / 0.4))` (ARAM threshold 0.6). Opponents are context only. There is no win bonus. Meeting all positive targets with zero deaths yields 100; both lane opponents can earn 100 independently.

Standard weights are damage 20%, participation 20%, survival 15%, economy 15%, vision 15%, objectives 15%. Support weights are combined damage + ally healing + shielding 20%, participation 25%, survival 20%, economy 10%, vision 20%, objectives 5%. ARAM excludes vision and objectives. Missing weights are rescaled; at least four metrics (three for ARAM) are needed. Role-specific targets and metric coverage appear on match pages. Unknown roles use an explicit general profile. Targets do not yet adjust for champion, rank, patch, or game phase. Scores are not official grades, percentiles, or rank estimates.

Startup recalculates every saved score from full match data. Old scores without full details are cleared until their details are imported, preventing mixed scoring versions in averages. The same v3 scorer is used for all participants, saved match rows, and aggregated stats.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/run
```

Tests mock Riot responses and do not require a real key.

API reference: https://developer.riotgames.com/apis/ · Routing and assets: https://developer.riotgames.com/docs/lol

History policy: only Ranked Solo/Duo (420) and Ranked Flex (440) matches lasting at least 180 seconds are stored. Early-surrender/remake flags are also excluded. Startup removes previously saved non-ranked games/remakes and resets the historical cursor once for ranked-only pagination; the existing import target is retained. Riot match-list queries use type=ranked; the storage boundary independently enforces queue and duration.

## Archetypes and calibration

Rift Score v3 uses the cached Riot catalog's primary champion tag plus role to select a provisional style. Tanks lower damage emphasis and add CC (damage taken is never rewarded); Mage/Marksman/Assassin carries emphasize damage and economy; Fighters use balanced combat weights. In Support, primary Tank selects tank support; primary Mage/Marksman/Assassin selects damage support without ally-healing requirements; other tagged supports use utility-support weights. Missing tags explicitly fall back to role weights. Solo-lane split overrides are listed in `app/archetypes.py`; they emphasize turret damage instead of generic objective damage and lower the KP target. These are app design choices, not official Riot classifications or calibrated population targets.

Match pages explain largest weighted contributions and largest gaps to full targets. `/calibration` shows your overall histogram, mean/median, P10/P90, standard deviation, floor/ceiling counts, and grouped champion/role/archetype samples. Review flags need 10 games and a mean at least 10 points from the overall mean; they identify differences to inspect, not proven bias or significance. No targets change automatically. Current cached catalog tags are used for historical matches. Startup recalculates all saved v3 scores; missing raw details leave scores unavailable until imported.
