from app.timeline import timeline_report
from app import storage


def fixture():
    return {'puuid': 'private', 'raw': {'info': {'gameDuration': 1100, 'participants': [
        {'puuid': 'private', 'participantId': 1, 'teamId': 100, 'teamPosition': 'TOP', 'championName': 'Teemo'},
        {'participantId': 6, 'teamId': 200, 'teamPosition': 'TOP', 'championName': 'Malphite'}]}}}


def test_irregular_frames_checkpoints_and_events():
    event = {'type': 'CHAMPION_KILL', 'timestamp': 550000, 'killerId': 6, 'victimId': 1}
    raw = {'info': {'frames': [{'timestamp': t, 'participantFrames': {'1': {'totalGold': 5000, 'xp': 4000, 'minionsKilled': 60, 'jungleMinionsKilled': 4}, '6': {'totalGold': 4500, 'xp': 4100, 'minionsKilled': 70}}, 'events': [event]} for t in (570000, 620000)]}}
    report = timeline_report(raw, fixture())
    assert report['checkpoints'][0]['point']['timestamp'] == 570000
    assert report['points'][0] == {'timestamp': 570000, 'gold': 500, 'xp': -100, 'cs': -6}
    assert report['checkpoints'][1]['point'] is None
    assert report['checkpoints'][2]['point'] is None
    assert len(report['events']) == 1 and report['events'][0]['involved']
    assert 'private' not in str(report)


def test_unknown_role_does_not_guess_opponent():
    stored = fixture(); stored['raw']['info']['participants'][0]['teamPosition'] = ''
    report = timeline_report({'info': {'frames': []}}, stored)
    assert report['opponent'] is None and report['points'] == []


def test_timeline_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DB', tmp_path / 'test.sqlite3')
    assert storage.timeline('a') is None
    storage.timeline('a', {'info': {'frames': []}})
    assert storage.timeline('a') == {'info': {'frames': []}}
