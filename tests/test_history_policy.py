import json
import pytest
from app import storage
from app.main import match_summary
from app.history_policy import eligible_info
from app.scoring import score_player
from test_scoring import game


@pytest.mark.parametrize('queue,duration,expected', [(420,179,False),(420,180,True),(440,181,True),(450,1800,False),(400,1800,False),(490,1800,False)])
def test_ranked_duration_boundary(queue, duration, expected):
    info = game()
    info.update(queueId=queue, gameDuration=duration)
    assert eligible_info(info) is expected
    raw = {'metadata': {'matchId': 'EU_test'}, 'info': info}
    assert (match_summary(raw, 'p0') is not None) is expected


def test_remake_flag_and_three_minute_score():
    info = game()
    info['gameDuration'] = 180
    assert score_player(info, info['participants'][0])['value'] == 50
    info['participants'][0]['gameEndedInEarlySurrender'] = True
    assert not eligible_info(info)
    assert score_player(info, info['participants'][0])['value'] is None


def test_storage_rejects_excluded_and_migration_removes_old_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DB', tmp_path / 'history.sqlite3')
    good = {'id': 'good', 'queue': 420, 'duration': 180, 'playedAt': 1}
    bad = {'id': 'bad', 'queue': 450, 'duration': 1200, 'playedAt': 2}
    short = {'id': 'short', 'queue': 440, 'duration': 179, 'playedAt': 3}
    assert storage.save_match('me', good)
    assert not storage.save_match('me', bad)
    assert not storage.save_match('me', short)
    with storage.connect() as db:
        for match in (bad, short):
            db.execute('INSERT INTO matches VALUES (?,?,?,?)', ('me', match['id'], match['playedAt'], json.dumps(match)))
    storage.save_state('me', {'offset':100,'recent_offset':20,'exhausted':True,'paused':True,'target':200,'end':1000})
    assert storage.apply_history_policy() == 2
    assert [m['id'] for m in storage.matches('me')] == ['good']
    state = storage.state('me')
    assert state['offset'] == 0 and not state['exhausted']
    assert state['paused'] and state['target'] == 200
    state['offset'] = 20
    storage.save_state('me', state)
    assert storage.apply_history_policy() == 0
    assert storage.state('me')['offset'] == 20
