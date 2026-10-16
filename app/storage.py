import json
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / 'data/journal.sqlite3'


def connect():
    DB.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB)
    db.execute('CREATE TABLE IF NOT EXISTS matches (player TEXT, id TEXT, played INTEGER, body TEXT, PRIMARY KEY(player,id))')
    db.execute('CREATE TABLE IF NOT EXISTS state (player TEXT PRIMARY KEY, body TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS profiles (player TEXT PRIMARY KEY, body TEXT)')
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
    return json.loads(row[0]) if row else {'target': 100, 'offset': 0, 'paused': False, 'exhausted': False}


def save_state(player, value):
    with connect() as db:
        db.execute('INSERT OR REPLACE INTO state VALUES (?,?)', (player, json.dumps(value)))


def save_match(player, match):
    with connect() as db:
        db.execute('INSERT OR REPLACE INTO matches VALUES (?,?,?,?)', (player, match['id'], match['playedAt'], json.dumps(match)))


def matches(player, queue=None):
    with connect() as db:
        rows = db.execute('SELECT body FROM matches WHERE player=? ORDER BY played DESC,id', (player,)).fetchall()
    result = [json.loads(row[0]) for row in rows]
    return [m for m in result if queue is None or m['queue'] == queue]
