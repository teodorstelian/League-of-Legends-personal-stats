import httpx
from fastapi.testclient import TestClient
from app.main import app, cache, match_summary


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
        assert any('queue=420' in url for url in calls)
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
    match = {'metadata': {'matchId': 'EU_1'}, 'info': {'gameDuration': 1200, 'participants': [
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
