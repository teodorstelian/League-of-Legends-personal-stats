# League metrics for Grafana

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.metrics:app --host 127.0.0.1 --port 8010
```

The exporter reads SQLite in read-only mode and uses `RIOT_ID` from `.env`,
independent of the profile selected in the web app. No Riot requests or API keys
are exposed. Refresh/import matches in Rift Journal to update the saved data.
Restart the exporter after rebooting Windows; automatic startup is not installed.

Grafana dashboards are maintained only in [Rig Pulse](https://github.com/teodorstelian/rig-pulse). This repository owns the exporter and its metric definitions; it does not distribute dashboard JSON copies.

In Rig Pulse's private `.env`, set:

```dotenv
ENABLE_LEAGUE_OF_LEGENDS=true
```

Then run `docker compose up -d --force-recreate` from the Rig Pulse repository. Prometheus fetches `host.docker.internal:8010/metrics` every 30 minutes. Keep this exporter running and ensure Docker Desktop can reach its bind address; adjust the bind address and firewall for your host if needed.

Open the [match dashboard](http://localhost:3000/d/rift-journal) or [champion mastery](http://localhost:3000/d/rift-journal-mastery). The canonical templates are [league-of-legends.json](https://github.com/teodorstelian/rig-pulse/blob/main/grafana/dashboards/league-of-legends.json) and [league-of-legends-mastery.json](https://github.com/teodorstelian/rig-pulse/blob/main/grafana/dashboards/league-of-legends-mastery.json). Edit dashboards in Rig Pulse and reapply its configuration.

Mastery comes from the saved profile snapshot across game modes, rather than imported ranked matches. Refresh the main account in Rift Journal to update it. Missing mastery snapshots produce an availability value of zero and no mastery totals; a saved empty snapshot has zero totals.

Metrics describe imported ranked history, not lifetime statistics. Scores skip
missing values and include valid zero scores. All metrics are gauges because
imports, deletions, and score recalculation can change them. Time series begin
when Prometheus starts scraping; old match dates are not backfilled. The latest
game panel shows the match start time, not the last API synchronization time.

Role metrics: the exporter now provides lol_role_* and lol_champion_role_* gauges by saved team position and ranked queue. Missing or unrecognized roles are UNKNOWN. Overall averages use covered matches, including valid zero scores. Grafana role dashboards and champion role filters are maintained only in Rig Pulse; update and restart this exporter for the new series. Mastery is not role-specific.

