import json
import sqlite3
from pathlib import Path
from .history_policy import eligible_summary, eligible_info
from .scoring import score_player, VERSION

DB = Path(__file__).resolve().parent.parent / 'data/journal.sqlite3'


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.execute('CREATE TABLE IF NOT EXISTS matches (player TEXT, id TEXT, played INTEGER, body TEXT, PRIMARY KEY(player,id))')
    db.execute('CREATE TABLE IF NOT EXISTS state (player TEXT PRIMARY KEY, body TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS profiles (player TEXT PRIMARY KEY, body TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS details (player TEXT, id TEXT, body TEXT, PRIMARY KEY(player,id))')
    db.execute('CREATE TABLE IF NOT EXISTS timelines (id TEXT PRIMARY KEY, body TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, body TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS timeline_meta (id TEXT PRIMARY KEY, unavailable INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS early_game_cache (player TEXT, id TEXT, body TEXT, PRIMARY KEY(player,id))')
    for action in ('INSERT', 'UPDATE'):
        db.execute(f"""CREATE TRIGGER IF NOT EXISTS timeline_meta_{action.lower()} AFTER {action} ON timelines BEGIN
            INSERT OR REPLACE INTO timeline_meta VALUES (NEW.id, COALESCE(json_extract(NEW.body, '$.unavailable'), 0));
            DELETE FROM early_game_cache WHERE id=NEW.id;
        END""")
        db.execute(f"""CREATE TRIGGER IF NOT EXISTS early_details_{action.lower()} AFTER {action} ON details BEGIN
            DELETE FROM early_game_cache WHERE player=NEW.player AND id=NEW.id;
        END""")
    db.execute('''CREATE TRIGGER IF NOT EXISTS early_details_delete AFTER DELETE ON details BEGIN
        DELETE FROM early_game_cache WHERE player=OLD.player AND id=OLD.id; END''')
    db.execute('''CREATE TRIGGER IF NOT EXISTS timeline_meta_delete AFTER DELETE ON timelines BEGIN
        DELETE FROM timeline_meta WHERE id=OLD.id;
        DELETE FROM early_game_cache WHERE id=OLD.id; END''')
    return db


def setting(name, value=None):
    with connect() as db:
        if value is not None:
            db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', (name, json.dumps(value)))
            return value
        row = db.execute('SELECT body FROM settings WHERE name=?', (name,)).fetchone()
    return json.loads(row[0]) if row else None


def timeline(match_id, value=None):
    with connect() as db:
        if value is not None:
            db.execute('INSERT OR REPLACE INTO timelines VALUES (?,?)', (match_id, json.dumps(value)))
            return value
        row = db.execute('SELECT body FROM timelines WHERE id=?', (match_id,)).fetchone()
    return json.loads(row[0]) if row else None


def timeline_rows(player):
    """Only timelines belonging to the player's currently eligible history."""
    with connect() as db:
        rows = db.execute('SELECT m.body,d.body,t.body FROM matches m LEFT JOIN details d ON m.player=d.player AND m.id=d.id LEFT JOIN timelines t ON t.id=m.id WHERE m.player=? ORDER BY m.played DESC', (player,)).fetchall()
    return [(json.loads(m), json.loads(d) if d else None, json.loads(t) if t else None) for m, d, t in rows if eligible_summary(json.loads(m))]


def match_details(player):
    with connect() as db:
        rows = db.execute('SELECT m.body,d.body FROM matches m LEFT JOIN details d ON m.player=d.player AND m.id=d.id WHERE m.player=? ORDER BY m.played DESC', (player,)).fetchall()
    return [(json.loads(m), json.loads(d) if d else None) for m, d in rows if eligible_summary(json.loads(m))]


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
            match['role'] = own.get('teamPosition') or 'UNKNOWN'
            match['items'] = [own.get(f'item{i}', 0) for i in range(7)]
            match['itemPatch'] = '.'.join(detail['raw']['info'].get('gameVersion', '').split('.')[:2])
            match['damage'] = own.get('totalDamageDealtToChampions')
            match['vision'] = own.get('visionScore')
            match['enemyChampionIds'] = sorted({p['championId'] for p in detail['raw']['info']['participants'] if p.get('teamId') != own.get('teamId')})
            role = own.get('teamPosition')
            opponents = [p for p in detail['raw']['info']['participants'] if role in ('TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY') and p.get('teamId') != own.get('teamId') and p.get('teamPosition') == role]
            match['opponentId'] = opponents[0]['championId'] if len(opponents) == 1 else None
            match['matchupStatus'] = 'matched' if len(opponents) == 1 else 'ambiguous'
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
        catalogs = {p: {c['championId']: c.get('tags') for c in json.loads(body).get('champions', [])} for p, body in db.execute('SELECT player,body FROM profiles').fetchall()}
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
                    score = score_player(info, own, catalogs.get(player, {}).get(own['championId']))
                    value['score'] = score['value']
                    value['archetype'] = score.get('archetype', 'Unscored')
                    value['scoreVersion'] = VERSION
                    db.execute('UPDATE matches SET body=? WHERE player=? AND id=?', (json.dumps(value), player, match_id))
            elif json.loads(body).get('scoreVersion') != VERSION:
                value = json.loads(body)
                value.update(score=None, scoreVersion=VERSION, archetype='Awaiting details')
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


# Keep this in sync with history_policy. JSON filtering touches small summaries only.
_ELIGIBLE_SQL = "json_extract(m.body,'$.queue') IN (420,440) AND json_extract(m.body,'$.duration') >= 180 AND NOT COALESCE(json_extract(m.body,'$.remake'),0)"


def _timeline_metadata(db):
    # One-time lazy backfill for old timelines; triggers maintain future changes.
    db.execute("""INSERT OR IGNORE INTO timeline_meta
        SELECT t.id,COALESCE(json_extract(t.body,'$.unavailable'),0) FROM timelines t
        LEFT JOIN timeline_meta meta ON meta.id=t.id WHERE meta.id IS NULL""")


def timeline_inventory(player):
    """Import status and pending IDs without loading raw timelines or details."""
    with connect() as db:
        _timeline_metadata(db)
        rows = db.execute(f"""SELECT m.id,d.id IS NOT NULL,meta.id IS NOT NULL,COALESCE(meta.unavailable,0)
            FROM matches m LEFT JOIN details d ON m.player=d.player AND m.id=d.id
            LEFT JOIN timeline_meta meta ON meta.id=m.id
            WHERE m.player=? AND {_ELIGIBLE_SQL}""", (player,)).fetchall()
    return {'total':len(rows), 'cached':sum(bool(t and not u) for _,_,t,u in rows),
            'unavailable':sum(bool(u) for _,_,_,u in rows),
            'pending':[mid for mid,d,t,u in rows if d and not t]}


def early_game_rows(player, now, queue='all', role='all', champion=0, period='all'):
    """Fetch matching compact summaries; parse raw timelines only for cache misses."""
    from .early_game import compact_timeline, COMPACT_VERSION
    conditions = ["m.player=?", _ELIGIBLE_SQL]
    args = [player]
    if queue != 'all':
        conditions.append("json_extract(m.body,'$.queue')=?"); args.append({'solo':420,'flex':440}[queue])
    if champion:
        conditions.append("json_extract(m.body,'$.championId')=?"); args.append(champion)
    if period == '30d':
        conditions.append("json_extract(m.body,'$.playedAt') BETWEEN ? AND ?"); args.extend([(now-30*86400)*1000,now*1000])
    result=[]
    pending=[]
    def flush(db):
        if not pending:
            return
        # Guard against source changes during parsing; commit only a short batch of writes.
        db.executemany('''INSERT OR REPLACE INTO early_game_cache (player,id,body)
            SELECT ?,?,? WHERE EXISTS (SELECT 1 FROM details WHERE player=? AND id=? AND body=?)
            AND EXISTS (SELECT 1 FROM timelines WHERE id=? AND body=?)''',pending)
        db.commit()
        pending.clear()
    with connect() as db:
        _timeline_metadata(db)
        records=db.execute(f"""SELECT m.body,d.id,c.body,meta.id,COALESCE(meta.unavailable,0)
            FROM matches m LEFT JOIN details d ON m.player=d.player AND m.id=d.id
            LEFT JOIN early_game_cache c ON c.player=m.player AND c.id=m.id
            LEFT JOIN timeline_meta meta ON meta.id=m.id
            WHERE {' AND '.join(conditions)} ORDER BY m.played DESC""",args).fetchall()
        db.commit()
        for body,detail_id,cached,timeline_id,unavailable in records:
            if cached:
                candidate=json.loads(cached)
                if candidate.get('report') is not None and candidate['report'].get('version') != COMPACT_VERSION:
                    cached=None
            match=json.loads(body)
            if cached:
                small=json.loads(cached)
            elif detail_id:
                detail_body=db.execute('SELECT body FROM details WHERE player=? AND id=?',(player,detail_id)).fetchone()
                if not detail_body:
                    continue
                detail=json.loads(detail_body[0])
                own=next((p for p in detail['raw']['info']['participants'] if p.get('puuid')==detail['puuid']),{})
                recorded=own.get('teamPosition')
                recorded=recorded if recorded in ('TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY') else 'UNKNOWN'
                small={'role':recorded,'report':None}
                # Role filtering precedes expensive timeline loading, including cold-cache requests.
                raw=None
                if timeline_id and not unavailable and (role=='all' or recorded==role):
                    raw=db.execute('SELECT body FROM timelines WHERE id=?',(match['id'],)).fetchone()
                    if raw:
                        small['report']=compact_timeline(json.loads(raw[0]),detail)
                # Only persist successful reports; missing/unavailable sources are cheap to inspect.
                if raw is not None and small['report'] is not None:
                    pending.append((player,match['id'],json.dumps(small),player,match['id'],detail_body[0],match['id'],raw[0]))
                    if len(pending)>=25:
                        flush(db)
            else:
                small={'role':match.get('role','UNKNOWN'),'report':None}
            match={**match,'role':small['role']}
            if role!='all' and match['role']!=role:
                continue
            report=small['report']
            result.append((match,None,{'unavailable':True} if unavailable else {'earlyReport':report} if report is not None else None))
        flush(db)
    return result
