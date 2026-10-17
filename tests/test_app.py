import httpx
import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app, cache, match_summary, sync_worker


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr('app.storage.DB', tmp_path / 'test.sqlite3')
    async def idle(client):
        await asyncio.Event().wait()
    monkeypatch.setattr('app.main.sync_worker', idle)


def test_missing_key(monkeypatch):
    monkeypatch.setattr('app.main.load_dotenv', lambda *a, **kw: None)
    monkeypatch.delenv('RIOT_API_KEY', raising=False)
    with TestClient(app) as client:
        assert client.get('/').status_code == 200
        response = client.get('/api/dashboard')
    assert response.status_code == 503
    assert response.json()['setup'] is True


def test_dashboard_routing_and_cache(monkeypatch):
    monkeypatch.setattr('app.main.load_dotenv', lambda *a, **kw: None)
    monkeypatch.setenv('RIOT_API_KEY', 'test-secret')
    monkeypatch.setenv('RIOT_ID', 'Bagabondu#1909')
    cache.clear()
    calls = []
    def handler(request):
        calls.append(str(request.url))
        if request.url.host.endswith('api.riotgames.com'):
            assert request.headers['X-Riot-Token'] == 'test-secret'
        else:
            assert 'X-Riot-Token' not in request.headers
        path = request.url.path
        if '/by-riot-id/' in path:
            assert request.url.host == 'europe.api.riotgames.com'
            body = {'puuid': 'player', 'gameName': 'Bagabondu', 'tagLine': '1909'}
        elif '/summoner/' in path:
            assert request.url.host == 'eun1.api.riotgames.com'
            body = {'summonerLevel': 100, 'profileIconId': 1}
        elif '/champion-mastery/' in path:
            body = [{'championId': 1, 'championPoints': 500, 'championLevel': 2}]
        elif '/league/' in path:
            assert request.url.host == 'eun1.api.riotgames.com'
            body = [{'queueType': 'RANKED_SOLO_5x5', 'tier': 'GOLD', 'rank': 'II', 'leaguePoints': 42, 'wins': 12, 'losses': 8}]
        elif '/ids' in path:
            body = []
        elif 'versions' in path:
            body = ['test']
        else:
            body = {'data': {'Annie': {'key': '1', 'name': 'Annie', 'image': {'full': 'Annie.png'}}}}
        return httpx.Response(200, json=body)
    with TestClient(app) as client:
        original = app.state.client
        app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        first = client.get('/api/dashboard')
        count = len(calls)
        assert client.get('/api/dashboard').json() == first.json()
        assert len(calls) == count
        solo = client.get('/api/dashboard?queue=solo')
        assert solo.json()['queue'] == 'solo'
        assert solo.json()['matches'] == []
        count = len(calls)
        assert client.get('/api/dashboard?queue=solo').json() == solo.json()
        assert len(calls) == count
        assert client.get('/api/dashboard?queue=invalid').status_code == 422
        assert len(calls) == count
        app.state.client = original
    assert first.status_code == 200
    assert first.json()['mastery'][0]['name'] == 'Annie'
    assert first.json()['ranked'][0]['lp'] == 42
    assert first.json()['ranked'][1]['tier'] is None
    assert 'test-secret' not in first.text


def test_match_summary():
    match = {'metadata': {'matchId': 'EU_1'}, 'info': {'gameDuration': 1200, 'queueId': 420, 'participants': [
        {'puuid': 'me', 'championName': 'Annie', 'championId': 1, 'win': True, 'kills': 5, 'deaths': 0, 'assists': 9, 'totalMinionsKilled': 100, 'neutralMinionsKilled': 5}]}}
    assert match_summary(match, 'me')['cs'] == 105
    assert match_summary(match, 'someone-else') is None


def test_rejected_key(monkeypatch):
    monkeypatch.setattr('app.main.load_dotenv', lambda *a, **kw: None)
    monkeypatch.setenv('RIOT_API_KEY', 'invalid')
    cache.clear()
    with TestClient(app) as client:
        original = app.state.client
        app.state.client = httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(403)))
        response = client.get('/api/dashboard')
        app.state.client = original
    assert response.status_code == 503
    assert 'rejected' in response.json()['message']


def test_champion_pages_filter_matches_and_handle_unplayed(monkeypatch):
    async def fake_dashboard(queue):
        return {'champions': [{'championId': 1, 'name': 'Annie'}, {'championId': 2, 'name': 'Olaf'}],
                'mastery': [{'championId': 1, 'points': 500, 'level': 2}],
                'matches': [{'championId': 1, 'id': 'one'}, {'championId': 2, 'id': 'two'}],
                'riotId': 'Test#EU', 'warning': None, 'updatedAt': 123}
    monkeypatch.setattr('app.main.get_dashboard', fake_dashboard)
    with TestClient(app) as client:
        assert client.get('/champions/1').status_code == 200
        response = client.get('/api/champions/1?queue=solo')
        assert response.status_code == 200
        body = response.json()
        assert body['queue'] == 'solo'
        assert body['matches'] == [{'championId': 1, 'id': 'one'}]
        assert body['sampleSize'] == 2
        assert body['mastery']['points'] == 500
        assert client.get('/api/champions/2').json()['mastery'] == {'points': 0, 'level': 0}
        assert client.get('/api/champions/9999').status_code == 404
        assert client.get('/api/champions/1?queue=invalid').status_code == 422


def test_storage_and_sync_controls():
    from app import storage
    player = 'Bagabondu#1909'
    match = {'id': 'EU_1', 'playedAt': 100, 'queue': 420, 'duration': 1200}
    storage.save_match(player, match)
    storage.save_match(player, match)
    assert len(storage.matches(player)) == 1
    assert storage.matches(player, 450) == []
    assert storage.matches('other') == []
    with TestClient(app) as client:
        assert client.post('/api/sync/pause').json()['paused'] is True
        assert client.post('/api/sync/resume').json()['paused'] is False
        assert client.post('/api/sync/more').json()['target'] == 200
        assert client.get('/api/sync').json()['saved'] == 1


def test_worker_checkpoint_and_restart(monkeypatch):
    from app import storage
    monkeypatch.setattr('app.main.configuration', lambda: ('test-key', 'Test#EU'))
    async def profile(*args):
        return {'champions': []}
    monkeypatch.setattr('app.main.dashboard', profile)
    offsets = []
    async def fake_fetch(client, url, key):
        if '/by-riot-id/' in url:
            return {'puuid': 'me'}
        if '/ids?' in url:
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(url).query)
            assert query['type'] == ['ranked']
            offset = int(query['start'][0])
            if 'endTime' in query:
                offsets.append(offset)
            if offset == 20:
                raise asyncio.CancelledError()
            return [f'EU_{i}' for i in range(20)]
        match_id = url.rsplit('/', 1)[1]
        return {'metadata': {'matchId': match_id}, 'info': {'gameStartTimestamp': 100, 'gameDuration': 1200, 'queueId': 420,
                'participants': [{'puuid': 'me', 'championId': 1, 'championName': 'Annie',
                'win': True, 'kills': 1, 'deaths': 2, 'assists': 3}]}}
    monkeypatch.setattr('app.main.fetch', fake_fetch)
    async def run():
        with pytest.raises(asyncio.CancelledError):
            await sync_worker(None)
    asyncio.run(run())
    assert len(storage.matches('Test#EU')) == 20
    assert storage.state('Test#EU')['offset'] == 20
    boundary = storage.state('Test#EU')['end']
    offsets.clear()
    asyncio.run(run())
    assert offsets == [20]
    assert len(storage.matches('Test#EU')) == 20
    assert storage.state('Test#EU')['end'] == boundary


def test_saved_profile_serves_history_without_network(monkeypatch):
    from app import storage
    monkeypatch.setattr('app.main.configuration', lambda: ('unused', 'Test#EU'))
    monkeypatch.setattr('app.main.load_dotenv', lambda *args, **kwargs: None)
    monkeypatch.setenv('RIOT_API_KEY', 'unused')
    monkeypatch.setenv('RIOT_ID', 'Test#EU')
    storage.profile('Test#EU', {'queue': 'all', 'champions': [{'championId': 1, 'name': 'Annie', 'icon': 'icon'}]})
    storage.save_match('Test#EU', {'id': 'one', 'playedAt': 100, 'queue': 420, 'duration': 1200, 'championId': 1, 'score': 40, 'scoreVersion': '3', 'role': 'TOP'})
    storage.save_match('Test#EU', {'id': 'two', 'playedAt': 200, 'queue': 440, 'duration': 1200, 'championId': 1, 'score': 80, 'scoreVersion': '3', 'mode': 'CLASSIC'})
    async def no_network(*args, **kwargs):
        pytest.fail('Saved history should not wait for Riot')
    monkeypatch.setattr('app.main.fetch', no_network)
    with TestClient(app) as client:
        body = client.get('/api/dashboard?queue=solo').json()
    assert body['queue'] == 'solo'
    assert len(body['matches']) == 1
    assert body['matches'][0]['name'] == 'Annie'
    assert body['scoreStats']['average'] == 40
    assert body['champions'][0]['scoreStats']['average'] == 40
    assert body['lanes'][0]['average'] == 40


def test_match_details_use_saved_data_and_reject_unknown_matches(monkeypatch):
    from app import storage
    from test_scoring import game
    monkeypatch.setattr('app.main.configuration', lambda: ('', 'Test#EU'))
    info = game()
    raw = {'metadata': {'matchId': 'EU_1'}, 'info': info}
    storage.save_match('Test#EU', match_summary(raw, 'p0'))
    storage.detail('Test#EU', 'EU_1', {'raw': raw, 'puuid': 'p0'})
    cache[('assets', '16.20')] = ('https://ddragon.leagueoflegends.com/cdn/16.20.1',
        {'1001': {'name': 'Boots', 'image': {'full': '1001.png'}}},
        {4: {'name': 'Flash', 'image': {'full': 'SummonerFlash.png'}}},
        {8005: {'name': 'Press the Attack', 'icon': 'perk-images/Styles/Precision/PressTheAttack/PressTheAttack.png'}})
    async def no_network(*args, **kwargs):
        pytest.fail('Cached details should not require a key or Riot request')
    monkeypatch.setattr('app.main.fetch', no_network)
    with TestClient(app) as client:
        assert client.get('/matches/EU_1').status_code == 200
        assert client.get('/api/matches/unknown').status_code == 404
        response = client.get('/api/matches/EU_1')
    assert response.status_code == 200
    body = response.json()
    assert len(body['participants']) == 10
    own = next(p for p in body['participants'] if p['you'])
    from app.scoring import score_player
    assert own['score']['value'] == score_player(info, info['participants'][0])['value']
    assert own['score']['version'] == '3'
    assert own['items'][0]['name'] == 'Boots'
    assert own['spells'][0]['name'] == 'Flash'
    assert own['runes'][0]['name'] == 'Press the Attack'
    assert 'puuid' not in response.text


def test_tier_list_endpoint_queue_and_validation(monkeypatch):
    async def fake_dashboard(queue):
        return {'queue':queue, 'champions':[{'championId':1,'name':'Annie'}],
                'matches':[{'championId':1,'score':80,'role':'MIDDLE','win':True}]}
    monkeypatch.setattr('app.main.get_dashboard',fake_dashboard)
    with TestClient(app) as client:
        assert client.get('/tier-list').status_code == 200
        body = client.get('/api/tier-list?queue=flex&minimum=1').json()
        assert body['queue'] == 'flex'
        assert body['roles'][2]['tiers'][0]['champions'][0]['name'] == 'Annie'
        assert client.get('/api/tier-list?minimum=0').status_code == 422
        assert client.get('/api/tier-list?queue=aram').status_code == 422


def test_tier_list_last_30_days_filters_before_averaging(monkeypatch):
    now = 2_000_000_000
    monkeypatch.setattr('app.main.time.time', lambda: now)
    async def fake_dashboard(queue):
        return {'queue': queue, 'champions': [{'championId':1,'name':'Annie'}], 'matches': [
            {'championId':1,'score':80,'role':'MIDDLE','playedAt':now*1000},
            {'championId':1,'score':60,'role':'MIDDLE','playedAt':(now-30*86400)*1000},
            {'championId':1,'score':0,'role':'MIDDLE','playedAt':(now-30*86400)*1000-1}]}
    monkeypatch.setattr('app.main.get_dashboard', fake_dashboard)
    with TestClient(app) as client:
        recent = client.get('/api/tier-list?period=30d&minimum=1').json()
        assert recent['totalGames'] == 2
        assert recent['roles'][2]['tiers'][1]['champions'][0]['scoreStats']['average'] == 70
        assert client.get('/api/tier-list?minimum=1').json()['totalGames'] == 3
        assert client.get('/api/tier-list?period=invalid').status_code == 422


def test_trends_page_filters_and_validation(monkeypatch):
    import time
    async def fake_dashboard(queue):
        return {'queue':queue,'champions':[{'championId':1,'name':'Annie'}],
                'matches':[{'championId':1,'role':'TOP','score':70,'playedAt':int(time.time()*1000),'win':True}]}
    monkeypatch.setattr('app.main.get_dashboard',fake_dashboard)
    with TestClient(app) as client:
        assert client.get('/trends').status_code == 200
        body=client.get('/api/trends?queue=flex&role=TOP&champion=1').json()
        assert body['queue']=='flex' and body['current']['score']['value']==70
        assert client.get('/api/trends?role=UTILITY').json()['current']['total']==0
        assert client.get('/api/trends?champion=-1').status_code==422
        assert client.get('/api/trends?queue=aram').status_code==422


def test_calibration_route_and_queue(monkeypatch):
    async def fake_dashboard(queue):
        return {'queue':queue,'matches':[],'champions':[]}
    monkeypatch.setattr('app.main.get_dashboard',fake_dashboard)
    with TestClient(app) as client:
        assert client.get('/calibration').status_code==200
        body=client.get('/api/calibration?queue=solo').json()
        assert body['queue']=='solo' and body['version']=='3'
        assert body['overall']['count']==0
        assert client.get('/api/calibration?minimum=0').status_code==422


def test_matchup_endpoint_validation_and_queue(monkeypatch):
    async def fake_dashboard(queue):
        return {'queue':queue,'matches':[],'champions':[{'championId':17,'name':'Teemo'}]}
    monkeypatch.setattr('app.main.get_dashboard',fake_dashboard)
    with TestClient(app) as client:
        body=client.get('/api/champions/17/matchups?queue=solo&period=30d&role=TOP').json()
        assert body['queue']=='solo' and body['period']=='30d'
        assert body['rows']==[]
        assert client.get('/api/champions/9999/matchups').status_code==404
        assert client.get('/api/champions/17/matchups?role=unknown').status_code==422


def test_general_matchups_endpoint(monkeypatch):
    async def fake_dashboard(queue):return {'queue':queue,'matches':[],'champions':[]}
    monkeypatch.setattr('app.main.get_dashboard',fake_dashboard)
    with TestClient(app) as client:
        assert client.get('/matchups',follow_redirects=False).status_code==404
        page=client.get('/draft')
        assert page.status_code==200
        assert 'id="matchups"' in page.text
        assert 'draft-view-nav' not in page.text
        assert 'evidence-role' not in page.text
        assert 'id="evidence-pairs"' in page.text
        body=client.get('/api/matchups?queue=flex&minimum=1').json()
        assert body['queue']=='flex' and body['bans']==[] and body['banMinimum']==3
        assert client.get('/api/matchups?minimum=0').status_code==422
        assert client.get('/api/matchups?period=bad').status_code==422


def test_draft_endpoint_filters_and_validation(monkeypatch):
    async def fake_dashboard(queue):return {'queue':queue,'matches':[],'champions':[{'championId':1,'name':'Annie'}]}
    monkeypatch.setattr('app.main.get_dashboard',fake_dashboard)
    with TestClient(app) as client:
        assert client.get('/draft').status_code==200
        body=client.get('/api/draft?queue=solo&role=UTILITY&enemy=1').json()
        assert body['queue']=='solo' and body['role']=='UTILITY' and body['fallback']
        assert client.get('/api/draft?minimum=1').status_code==422
        assert client.get('/api/draft?enemy=9999').status_code==404
        assert client.get('/api/draft?role=all').status_code==422
