import json
import sqlite3
from scripts.validate_scoring import auc, audit
from app.scoring import VERSION, score_player
from test_scoring import game


def test_auc_handles_ties_and_direction():
    assert auc([]) is None
    assert auc([{'score': 5, 'win': True}]) is None
    assert auc([{'score': 5, 'win': True}, {'score': 5, 'win': False}]) == .5
    assert auc([{'score': 10, 'win': True}, {'score': 5, 'win': False}]) == 1
    assert auc([{'score': 1, 'win': True}, {'score': 5, 'win': False}]) == 0


def test_audit_is_read_only_and_deduplicates_shared_matches(tmp_path):
    path = tmp_path / 'audit.sqlite3'
    info = game()
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE profiles (player TEXT, body TEXT)')
        db.execute('CREATE TABLE matches (player TEXT, id TEXT, body TEXT)')
        db.execute('CREATE TABLE details (player TEXT, id TEXT, body TEXT)')
        for owner in ('a', 'b'):
            score = score_player(info, info['participants'][0])['value']
            db.execute('INSERT INTO profiles VALUES (?,?)', (owner, json.dumps({'champions': []})))
            db.execute('INSERT INTO matches VALUES (?,?,?)', (owner, 'shared', json.dumps({'score': score, 'scoreVersion': VERSION})))
            db.execute('INSERT INTO details VALUES (?,?,?)', (owner, 'shared', json.dumps({'raw': {'info': info}, 'puuid': 'p0'})))
    before = path.read_bytes()
    result = audit(path)
    assert path.read_bytes() == before
    assert result['uniqueMatches'] == 1
    assert result['allParticipants']['games'] == 10
    assert result['checks']['ownScoresChecked'] == 2
    assert result['checks']['monotonicChecks'] == 6
    assert result['checks']['savedScoreMismatches'] == 0
    assert result['checks']['monotonicFailures'] == 0
