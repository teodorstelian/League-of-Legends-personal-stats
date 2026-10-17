import asyncio
import pytest
from fastapi.testclient import TestClient
from app import storage
from app.early_game import early_game_report
from app.main import app, cached_timeline, timeline_worker, RiotError

NOW = 2_000_000_000


def row(id='a', gold=100, win=True, queue=420, age=0, role='TOP', champion=17, duration=1200):
    m = {'id': id, 'championId': champion, 'role': role, 'duration': duration, 'queue': queue, 'playedAt': (NOW-age*86400)*1000, 'win': win}
    d = {'puuid': 'private', 'raw': {'info': {'queueId': queue, 'gameDuration': duration, 'participants': [
        {'participantId': 1, 'championId': champion, 'puuid': 'private', 'teamId': 100, 'teamPosition': role, 'championName': 'Teemo'},
        {'participantId': 6, 'championId': 99, 'teamId': 200, 'teamPosition': role, 'championName': 'Enemy'}]}}}
    t = {'info': {'frames': [{'timestamp': minute*60000, 'participantFrames': {'1': {'totalGold': 5000+gold, 'xp': 3000}, '6': {'totalGold': 5000, 'xp': 3500}}, 'events': [{'type': 'CHAMPION_KILL', 'timestamp': 599999 if minute==10 else 600000, 'killerId': 6, 'victimId': 1}]} for minute in (10,15)]}}
    return m, d, t


def test_coverage_leads_conversion_and_deaths():
    a = row(); b = row('b', gold=-100, win=False); c = row('c', gold=200, win=False)
    missing = row('missing'); unavailable = row('404')
    report = early_game_report([a,b,c,(missing[0],missing[1],None),(unavailable[0],unavailable[1],{'unavailable':True})], NOW)
    assert report['total'] == 5 and report['cached'] == 3 and report['unavailable'] == 1
    cp = report['summary']['checkpoints'][0]
    assert cp['count'] == 3 and cp['leads'] == 2 and cp['conversion'] == 50
    assert cp['gold'] == 66.7 and cp['xp'] == -500
    assert report['summary']['earlyDeaths'] == 3
    assert report['summary']['deathsPerGame'] == 1
    assert 'private' not in str(report)


def test_filters_grouping_and_empty_samples():
    rows=[row(),row('old',age=31),row('flex',queue=440),row('jg',role='JUNGLE'),row('other',champion=1)]
    report=early_game_report(rows,NOW,queue='solo',role='TOP',champion=17,period='30d')
    assert report['total']==1 and len(report['champions'])==1 and report['roles'][0]['role']=='TOP'
    empty=early_game_report([],NOW)
    assert empty['summary']['checkpoints'][0]['gold'] is None
    assert empty['summary']['deathsPerGame'] is None


def test_old_summary_roles_use_match_details_before_filtering():
    missing = row(role='UTILITY')
    missing[0].pop('role')
    stale = row('stale', role='UTILITY')
    stale[0]['role'] = 'UNKNOWN'
    report = early_game_report([missing, stale], NOW, role='UTILITY')
    assert report['total'] == 2
    assert report['roles'][0]['role'] == 'UTILITY'
    assert report['champions'][0]['role'] == 'UTILITY'
    assert report['summary']['checkpoints'][0]['count'] == 2
    assert 'role' not in missing[0]


def test_short_games_and_unknown_roles_excluded_from_relevant_denominators():
    report=early_game_report([row(duration=500),row('unknown',role='UNKNOWN')],NOW)
    assert report['summary']['checkpoints'][0]['count']==0
    assert report['summary']['deathGames']==1


def test_manual_import_is_scoped_and_pause_preserves_pending(tmp_path, monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'test.sqlite3')
    monkeypatch.setattr('app.main.configuration',lambda: ('key','test'))
    async def idle(client): await asyncio.Event().wait()
    monkeypatch.setattr('app.main.sync_worker',idle)
    monkeypatch.setattr('app.main.timeline_worker',idle)
    m,d,t=row(); storage.save_match('test',m);storage.detail('test','a',d)
    storage.save_match('other',row('other')[0])
    with TestClient(app) as client:
        assert client.get('/early-game').status_code==200
        assert client.get('/api/early-game').json()['cached']==0
        assert client.get('/api/timeline-import').json()['active'] is False
        assert client.post('/api/timeline-import/start').json()['remaining']==1
        assert client.post('/api/timeline-import/pause').json()['active'] is False
        assert storage.state('test')['timelinePending']==['a']
        storage.timeline('a',t)
        assert client.get('/api/early-game').json()['cached']==1
        assert client.get('/api/early-game?queue=bad').status_code==422
        assert client.get('/api/matches/other/timeline').status_code==404


def test_cache_reuses_success_and_remembers_unavailable(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'test.sqlite3')
    calls=[]
    async def fetch(client,url,key):
        calls.append(url)
        if 'missing' in url: raise RiotError('not found',404)
        return {'info':{'frames':[]}}
    monkeypatch.setattr('app.main.fetch',fetch)
    async def run():
        await cached_timeline(None,'a','key');await cached_timeline(None,'a','key')
        assert (await cached_timeline(None,'missing','key'))['unavailable']
        await cached_timeline(None,'missing','key')
    asyncio.run(run())
    assert len(calls)==2


def test_worker_finishes_explicit_queue(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'test.sqlite3')
    monkeypatch.setattr('app.main.configuration',lambda: ('key','test'))
    state=storage.state('test');state.update(timelineActive=True,timelinePending=['a']);storage.save_state('test',state)
    async def fetch(client,url,key):return {'info':{'frames':[]}}
    monkeypatch.setattr('app.main.fetch',fetch)
    async def run():
        task=asyncio.create_task(timeline_worker(None))
        await asyncio.sleep(.05)
        assert storage.timeline('a') is not None
        assert not storage.state('test')['timelineActive']
        task.cancel()
        with pytest.raises(asyncio.CancelledError):await task
    asyncio.run(run())
