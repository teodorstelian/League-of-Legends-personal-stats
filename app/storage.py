import json
import sqlite3
from pathlib import Path
from .history_policy import eligible_summary, eligible_info
from .scoring import score_player

DB = Path(__file__).resolve().parent.parent / 'data/journal.sqlite3'


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.execute('CREATE TABLE IF NOT EXISTS matches (player TEXT, id TEXT, played INTEGER, body TEXT, PRIMARY KEY(player,id))')
    db.execute('CREATE TABLE IF NOT EXISTS state (player TEXT PRIMARY KEY, body TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS profiles (player TEXT PRIMARY KEY, body TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS details (player TEXT, id TEXT, body TEXT, PRIMARY KEY(player,id))')
    return db


def profile(player, value=None):
    with connect() as db:
        if value is not None:
            db.execute('INSERT OR REPLACE INTO profiles VALUES (?,?)', (player, json.dumps(value)))
            return value
        row = db.execute('SELECT body FROM profiles WHERE player=?', (player,)).fetchone()
    return json.loads(row[0]) if row else None


def state(player):
    with connect() as db:
        row = db.execute('SELECT body FROM state WHERE player=?', (player,)).fetchone()
    return json.loads(row[0]) if row else {'target': 100, 'offset': 0, 'paused': False, 'exhausted': False, 'historyPolicy': 2}


def save_state(player, value):
    with connect() as db:
        db.execute('INSERT OR REPLACE INTO state VALUES (?,?)', (player, json.dumps(value)))


def save_match(player, match):
    if not eligible_summary(match):
        return False
    with connect() as db:
        db.execute('INSERT OR REPLACE INTO matches VALUES (?,?,?,?)', (player, match['id'], match['playedAt'], json.dumps(match)))
    return True


def matches(player, queue=None):
    with connect() as db:
        rows = db.execute('SELECT m.body,d.body FROM matches m LEFT JOIN details d ON m.player=d.player AND m.id=d.id WHERE m.player=? ORDER BY m.played DESC,m.id', (player,)).fetchall()
    result = []
    for body, detail_body in rows:
        match = json.loads(body)
        if detail_body:
            detail = json.loads(detail_body)
            own = next((p for p in detail['raw']['info']['participants'] if p.get('puuid') == detail['puuid']), {})
            match.setdefault('role', own.get('teamPosition') or 'UNKNOWN')
            match['items'] = [own.get(f'item{i}', 0) for i in range(7)]
            match['itemPatch'] = '.'.join(detail['raw']['info'].get('gameVersion', '').split('.')[:2])
        if eligible_summary(match):
            result.append(match)
    return [m for m in result if queue is None or m['queue'] == queue]


def detail(player, match_id, value=None):
    with connect() as db:
        if value is not None:
            if not eligible_info(value['raw']['info']):
                return None
            db.execute('INSERT OR REPLACE INTO details VALUES (?,?,?)', (player, match_id, json.dumps(value)))
            return value
        row = db.execute('SELECT body FROM details WHERE player=? AND id=?', (player, match_id)).fetchone()
    return json.loads(row[0]) if row else None


def pending(player, limit=20):
    with connect() as db:
        return [r[0] for r in db.execute('SELECT m.id FROM matches m LEFT JOIN details d ON m.player=d.player AND m.id=d.id WHERE m.player=? AND d.id IS NULL ORDER BY m.played DESC LIMIT ?', (player, limit))]


def apply_history_policy():
    """Remove excluded history and reset pagination once for ranked-only imports."""
    removed = 0
    with connect() as db:
        for player, match_id, body, raw_body in db.execute('SELECT m.player,m.id,m.body,d.body FROM matches m LEFT JOIN details d ON m.player=d.player AND m.id=d.id').fetchall():
            keep = eligible_summary(json.loads(body))
            if raw_body:
                keep = keep and eligible_info(json.loads(raw_body)['raw']['info'])
            if not keep:
                db.execute('DELETE FROM matches WHERE player=? AND id=?', (player, match_id))
                db.execute('DELETE FROM details WHERE player=? AND id=?', (player, match_id))
                removed += 1
            elif raw_body:
                value = json.loads(body)
                detail = json.loads(raw_body)
                info = detail['raw']['info']
                own = next((p for p in info['participants'] if p.get('puuid') == detail['puuid']), None)
                if own:
                    value['score'] = score_player(info, own)['value']
                    value['scoreVersion'] = '2'
                    db.execute('UPDATE matches SET body=? WHERE player=? AND id=?', (json.dumps(value), player, match_id))
            elif json.loads(body).get('scoreVersion') != '2':
                value = json.loads(body)
                value.update(score=None, scoreVersion='2')
                db.execute('UPDATE matches SET body=? WHERE player=? AND id=?', (json.dumps(value), player, match_id))
        db.execute('DELETE FROM details WHERE NOT EXISTS (SELECT 1 FROM matches m WHERE m.player=details.player AND m.id=details.id)')
        for player, body in db.execute('SELECT player,body FROM profiles').fetchall():
            value = json.loads(body)
            value['matches'] = []
            db.execute('UPDATE profiles SET body=? WHERE player=?', (json.dumps(value), player))
        for player, body in db.execute('SELECT player,body FROM state').fetchall():
            value = json.loads(body)
            if value.get('historyPolicy') != 2:
                value.update(offset=0, recent_offset=0, exhausted=False, historyPolicy=2)
                value.pop('end', None)
                db.execute('UPDATE state SET body=? WHERE player=?', (json.dumps(value), player))
    return removed
