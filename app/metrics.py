"""Read-only Prometheus exporter for the configured main account's saved history.

Run: python -m uvicorn app.metrics:app --host 127.0.0.1 --port 8010
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import Response

from . import storage

app = FastAPI(title='Rift Journal metrics', docs_url=None, redoc_url=None)


def render_metrics(player, matches, profile=None):
    lines = []

    def gauge(name, help_text, values):
        name = 'lol_' + name
        lines.extend([f'# HELP {name} {help_text}', f'# TYPE {name} gauge'])
        for labels, value in values:
            if value is not None:
                labels = {'player': player, **labels}
                label_text = ','.join(f'{k}={json.dumps(str(v), ensure_ascii=False)}' for k, v in labels.items())
                lines.append(f'{name}{{{label_text}}} {float(value)}')

    groups = [({'queue': 'all'}, matches)]
    groups += [({'queue': name}, [m for m in matches if m['queue'] == queue])
               for name, queue in [('solo', 420), ('flex', 440)]]
    gauge('saved_games', 'Number of imported ranked matches; not lifetime games.', [(l, len(ms)) for l, ms in groups])
    gauge('win_rate_percent', 'Win percentage over imported matches.', [(l, 100 * sum(m['win'] for m in ms) / len(ms)) for l, ms in groups if ms])
    for field in ('kills', 'deaths', 'assists', 'score'):
        values = []
        for labels, ms in groups:
            samples = [m[field] for m in ms if m.get(field) is not None]
            if samples:
                values.append((labels, sum(samples) / len(samples)))
        gauge('average_' + field, 'Average ' + field + ' over covered saved matches.', values)
    gauge('scored_games', 'Saved matches with a Rift Score.', [(l, sum(m.get('score') is not None for m in ms)) for l, ms in groups])
    champions = sorted({m['champion'] for m in matches})
    for field in ('games', 'win_rate_percent', 'score'):
        values = []
        for champion in champions:
            ms = [m for m in matches if m['champion'] == champion]
            scores = [m['score'] for m in ms if m.get('score') is not None]
            value = len(ms) if field == 'games' else (100 * sum(m['win'] for m in ms) / len(ms) if field == 'win_rate_percent' else (sum(scores) / len(scores) if scores else None))
            values.append(({'champion': champion}, value))
        gauge('champion_' + field, 'Saved champion ' + field + '.', values)
    latest = max(matches, key=lambda m: m['playedAt'], default=None)
    gauge('latest_match_timestamp_seconds', 'Start time of newest saved match, Unix seconds.', [({}, latest['playedAt'] / 1000)] if latest else [])
    mastery = (profile or {}).get('mastery')
    gauge('mastery_available', 'Whether a saved mastery snapshot is available.', [({}, int(mastery is not None))])
    if mastery is not None:
        for field in ('points', 'level'):
            gauge('mastery_' + field, 'Latest saved champion mastery ' + field + '.',
                  [({'champion': m.get('name') or str(m['championId']), 'champion_id': m['championId']}, m.get(field))
                   for m in mastery])
        gauge('mastery_combined_points', 'Total mastery points in the saved Riot snapshot.',
              [({}, sum(m.get('points', 0) for m in mastery))])
        gauge('mastery_champions', 'Number of champions with positive mastery points.',
              [({}, sum(m.get('points', 0) > 0 for m in mastery))])
    # ID-based series join match summaries to mastery despite display-name differences.
    catalog = {int(c['championId']): c.get('name') for c in (profile or {}).get('champions', [])}
    catalog.update({int(c['championId']): c.get('name') for c in (mastery or []) if c.get('name')})
    detail_values = {field: [] for field in ('games', 'wins', 'losses', 'scored_games',
                                             'kills', 'deaths', 'assists', 'score')}
    champion_ids = sorted({int(m['championId']) for m in matches if m.get('championId') is not None})
    for champion_id in champion_ids:
        champion_matches = [m for m in matches if m.get('championId') is not None and int(m['championId']) == champion_id]
        name = catalog.get(champion_id) or champion_matches[0]['champion']
        for queue_name, queue_id in [('all', None), ('solo', 420), ('flex', 440)]:
            ms = [m for m in champion_matches if queue_id is None or m['queue'] == queue_id]
            labels = {'champion': name, 'champion_id': champion_id, 'queue': queue_name}
            totals = {'games': len(ms), 'wins': sum(bool(m['win']) for m in ms),
                      'losses': sum(not m['win'] for m in ms),
                      'scored_games': sum(m.get('score') is not None for m in ms)}
            for field, value in totals.items():
                detail_values[field].append((labels, value))
            for field in ('kills', 'deaths', 'assists', 'score'):
                samples = [m[field] for m in ms if m.get(field) is not None]
                if samples:
                    detail_values[field].append((labels, sum(samples) / len(samples)))
    for field, values in detail_values.items():
        gauge('champion_detail_' + field, 'Saved ranked champion ' + field + '; filtered by queue. Averages omit missing values.', values)
    # Separate role series preserve existing champion/overview metric contracts.
    roles = ('TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY', 'UNKNOWN')
    def role_of(match):
        value = str(match.get('role') or '').upper()
        return value if value in roles else 'UNKNOWN'

    def summaries(prefix, subsets):
        fields = {field: [] for field in ('games', 'wins', 'losses', 'scored_games',
                                          'kills', 'deaths', 'assists', 'score')}
        for labels, ms in subsets:
            for field, value in {'games': len(ms), 'wins': sum(bool(m['win']) for m in ms),
                                 'losses': sum(not m['win'] for m in ms),
                                 'scored_games': sum(m.get('score') is not None for m in ms)}.items():
                fields[field].append((labels, value))
            for field in ('kills', 'deaths', 'assists', 'score'):
                samples = [m[field] for m in ms if m.get(field) is not None]
                if samples:
                    fields[field].append((labels, sum(samples) / len(samples)))
        for field, values in fields.items():
            gauge(prefix + field, 'Saved ranked ' + field + ' by queue and reported role; averages skip missing values.', values)

    role_subsets, champion_role_subsets = [], []
    for queue_name, queue_id in [('all', None), ('solo', 420), ('flex', 440)]:
        queue_matches = [m for m in matches if queue_id is None or m['queue'] == queue_id]
        for role in ('all', *roles):
            ms = [m for m in queue_matches if role == 'all' or role_of(m) == role]
            role_subsets.append(({'queue': queue_name, 'role': role}, ms))
            for champion_id in champion_ids:
                cms = [m for m in ms if m.get('championId') is not None and int(m['championId']) == champion_id]
                # Unknown/empty combinations remain unavailable, not invented zero samples.
                if not cms:
                    continue
                name = catalog.get(champion_id) or cms[0]['champion']
                champion_role_subsets.append(({'champion': name, 'champion_id': champion_id,
                                              'queue': queue_name, 'role': role}, cms))
    summaries('role_', role_subsets)
    summaries('champion_role_', champion_role_subsets)
    return '\n'.join(lines) + '\n'


@app.get('/metrics')
def metrics():
    load_dotenv(Path(__file__).resolve().parent.parent / '.env', override=True)
    player = os.getenv('RIOT_ID', 'Bagabondu#1909').strip()
    # Avoid storage.connect(): scraping must never create or modify the journal.
    import sqlite3
    with sqlite3.connect(storage.DB.resolve().as_uri() + '?mode=ro', uri=True) as db:
        rows = db.execute('SELECT body FROM matches WHERE player=?', (player,)).fetchall()
        profile_row = db.execute('SELECT body FROM profiles WHERE player=?', (player,)).fetchone()
    from .history_policy import eligible_summary
    matches = [json.loads(row[0]) for row in rows]
    return Response(render_metrics(player, [m for m in matches if eligible_summary(m)],
                                   json.loads(profile_row[0]) if profile_row else None),
                    media_type='text/plain; version=0.0.4')
