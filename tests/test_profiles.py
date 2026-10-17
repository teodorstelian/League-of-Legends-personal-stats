import asyncio
from fastapi.testclient import TestClient
from app import storage
from app.main import app, configuration


def test_environment_profiles_work_with_fresh_database(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DB', tmp_path / 'fresh.sqlite3')
    monkeypatch.setattr('app.main.load_dotenv', lambda *a, **kw: None)
    monkeypatch.setenv('RIOT_ID', 'First#EU')
    monkeypatch.setenv('DUO_RIOT_ID', 'Duo#EU')
    async def idle(client): await asyncio.Event().wait()
    monkeypatch.setattr('app.main.sync_worker', idle)
    monkeypatch.setattr('app.main.timeline_worker', idle)
    with TestClient(app) as client:
        profiles = client.get('/api/profiles').json()
        assert [p['riotId'] for p in profiles['profiles']] == ['First#EU', 'Duo#EU']
        assert client.get('/api/duo').json()['profiles'] == ['First#EU', 'Duo#EU']
        client.post('/api/profiles/select', json={'riotId':'duo#eu'})
        assert len(client.get('/api/profiles').json()['profiles']) == 2
        assert client.get('/api/duo').json()['profiles'] == ['Duo#EU','First#EU']


def test_profile_selection_persists_and_isolates_data(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, 'DB', tmp_path / 'profiles.sqlite3')
    monkeypatch.setattr('app.main.load_dotenv', lambda *a, **kw: None)
    monkeypatch.setenv('RIOT_ID', 'First#EU')
    monkeypatch.delenv('DUO_RIOT_ID', raising=False)
    async def idle(client): await asyncio.Event().wait()
    monkeypatch.setattr('app.main.sync_worker', idle)
    monkeypatch.setattr('app.main.timeline_worker', idle)
    storage.save_match('First#EU', {'id':'first', 'queue':420, 'duration':900, 'playedAt':1, 'championId':17})
    storage.save_match('Second#EU', {'id':'second', 'queue':420, 'duration':900, 'playedAt':1, 'championId':1})
    with TestClient(app) as client:
        assert client.get('/api/profiles').json()['active'] == 'First#EU'
        assert client.post('/api/profiles/select', json={'riotId':'Second#EU'}).json()['active'] == 'Second#EU'
        assert configuration()[1] == 'Second#EU'
        assert client.get('/api/early-game').json()['total'] == 1
        assert client.get('/api/matches/first/timeline').status_code == 404
        assert client.post('/api/profiles/select', json={'riotId':'second#eu'}).json()['active'] == 'Second#EU'
        assert len(client.get('/api/profiles').json()['profiles']) == 2
        assert client.get('/duo').status_code == 200
        duo = client.get('/api/duo').json()
        assert duo['profiles'] == ['Second#EU','First#EU']
        assert not duo['ready']
        assert client.get('/api/duo?partner=Unknown%23EU').status_code == 400
        assert client.get('/api/duo?queue=bad').status_code == 422
        assert client.post('/api/profiles/select', json={'riotId':'invalid'}).status_code == 400
        assert client.post('/api/profiles/select', json={'riotId':'First#EU'}).status_code == 200
        assert client.get('/api/matches/second/timeline').status_code == 404
    assert len(storage.matches('First#EU')) == 1
    assert len(storage.matches('Second#EU')) == 1
