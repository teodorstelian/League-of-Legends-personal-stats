from app.calibration import distribution, calibration_report


def test_distribution_includes_100_and_excludes_missing():
    stats=distribution([{'score':v} for v in [0,10,50,100,None]])
    assert stats['count']==4 and stats['total']==5
    assert stats['mean']==40 and stats['median']==30
    assert stats['histogram']==[1,1,0,0,0,1,0,0,0,1]
    assert stats['floor']==1 and stats['ceiling']==1
    assert distribution([])['mean'] is None


def test_review_flags_need_sample_and_do_not_change_scores():
    data={'matches':[{'score':80,'role':'TOP','archetype':'Tank','championId':1} for _ in range(10)]+[{'score':20,'role':'UTILITY','archetype':'Utility support','championId':2} for _ in range(10)],'champions':[{'championId':1,'name':'A'},{'championId':2,'name':'B'}]}
    result=calibration_report(data)
    assert result['overall']['mean']==50
    assert result['roles'][0]['review'] is True
    assert result['champions'][0]['count']==10
    assert data['matches'][0]['score']==80


def test_duration_role_baseline_and_extremes():
    matches = [
        {'id': 'a', 'score': 80, 'role': 'TOP', 'championId': 1, 'duration': 1199, 'playedAt': 1},
        {'id': 'b', 'score': 40, 'role': 'UTILITY', 'championId': 1, 'duration': 1200, 'playedAt': 2},
        {'id': 'c', 'score': 40, 'role': 'TOP', 'championId': 2, 'duration': 1800, 'playedAt': 3},
        {'id': 'd', 'score': 80, 'role': 'UTILITY', 'championId': 2, 'duration': 2400, 'playedAt': 4},
        {'id': 'e', 'score': None, 'role': 'TOP', 'championId': 1},
        {'id': 'f', 'score': 100, 'role': 'UNKNOWN', 'championId': 1, 'duration': -1},
    ]
    result = calibration_report({'matches': matches, 'champions': [{'championId': 1, 'name': 'A'}]}, 1)
    champion = result['champions'][0]
    assert champion['roleReference'] == 60
    assert champion['roleDifference'] == 0
    assert champion['roleComparedGames'] == 2
    assert [r['count'] for r in result['durations']] == [1, 1, 1, 1]
    assert [m['id'] for m in result['extremes']['highest']][:3] == ['f', 'd', 'a']
    assert [m['id'] for m in result['extremes']['lowest']][:2] == ['c', 'b']
    assert result['componentGames'] == 0
    assert result['components'] == []


def test_components_use_own_participant_and_available_metric_denominators():
    from test_scoring import game
    info = game()
    own = info['participants'][0]
    own['deaths'] = 0
    own['damageDealtToObjectives'] = 0
    other = game()
    del other['participants'][0]['visionScore']
    matches = [{'id': key, 'score': 50, 'role': 'TOP', 'championId': 1} for key in ['a', 'b', 'missing']]
    details = {key: {'raw': {'info': value}, 'puuid': 'p0'} for key, value in [('a', info), ('b', other)]}
    result = calibration_report({'matches': matches, 'champions': []}, details=details)
    assert result['componentGames'] == 2
    overall = {r['name']: r for r in result['components'] if r['scope'] == 'Overall'}
    assert overall['Vision']['count'] == 1
    assert overall['Survival']['hundredPercent'] == 50
    assert overall['Objective pressure']['zeroPercent'] == 50
    assert set(r['scope'] for r in result['components']) == {'Overall', 'Role', 'Archetype'}


def test_empty_diagnostics():
    result = calibration_report({'matches': [], 'champions': []})
    assert result['extremes'] == {'highest': [], 'lowest': []}
    assert all(r['count'] == 0 for r in result['durations'])


def test_calibration_endpoint_uses_selected_profile_and_queue(monkeypatch):
    import app.main as main
    calls = []
    monkeypatch.setattr(main, 'configuration', lambda: ('key', 'selected#profile'))
    async def dashboard(queue):
        calls.append(queue)
        return {'queue': queue, 'matches': [], 'champions': []}
    def details(owner):
        calls.append(owner)
        return []
    monkeypatch.setattr(main, 'get_dashboard', dashboard)
    monkeypatch.setattr(main.storage, 'match_details', details)
    request = main.get_calibration('flex', 10)
    try:
        request.send(None)
    except StopIteration as completed:
        result = completed.value
    else:
        raise AssertionError('Mocked endpoint unexpectedly suspended')
    assert calls == ['flex', 'selected#profile']
    assert result['queue'] == 'flex' and result['minimum'] == 10


def test_investigation_pairs_outcomes_and_isolates_cc_change():
    from copy import deepcopy
    from test_scoring import game
    from app.scoring import score_player
    matches, details = [], {}
    for key, role, win, duration in [('tank', 'TOP', True, 1199), ('support', 'UTILITY', False, 1800), ('carry', 'BOTTOM', True, 2400)]:
        info = game()
        info['gameDuration'] = duration
        own = info['participants'][0]
        own.update(teamPosition=role, timeCCingOthers=duration / 60 * 1.5)
        champion_id = 2 if key == 'carry' else 1
        own['championId'] = champion_id
        matches.append({'id': key, 'role': role, 'win': win, 'duration': duration, 'score': 50, 'championId': champion_id})
        details[key] = {'raw': {'info': info}, 'puuid': 'p0'}
    original = deepcopy(details)
    result = calibration_report({'matches': matches, 'champions': [{'championId': 1, 'name': 'Tank', 'tags': ['Tank']}, {'championId': 2, 'name': 'Carry', 'tags': ['Marksman']}]}, details=details)
    investigation = result['investigation']
    groups = {r['name']: r for r in investigation['comparisons']}
    assert groups['Tank']['delta'] < 0
    assert groups['Tank support']['delta'] < 0
    assert groups['Marksman carry']['delta'] == 0
    assert len(investigation['examples']) == 2
    assert all(r['currentCap'] == 0 and r['candidateCap'] == 0 for r in investigation['cc'])
    duration = {r['name']: r for r in investigation['durationResults']}
    assert duration['Under 20 min · Win']['count'] == 1
    assert duration['Under 20 min · Loss']['current'] is None
    assert duration['30–39:59 min · Loss']['count'] == 1
    assert duration['40+ min · Win']['count'] == 1
    assert all(r['count'] == 1 for r in investigation['durationComponents'])
    assert details == original
    assert all(m['score'] == 50 for m in matches)
    info = details['tank']['raw']['info']
    current = score_player(info, info['participants'][0], ['Tank'])
    candidate = score_player(info, info['participants'][0], ['Tank'], cc_target=3)
    assert current['value'] > candidate['value']
    assert current == score_player(info, info['participants'][0], ['Tank'])


def test_short_game_flags_include_unscorable_details_and_unknowns():
    from test_scoring import game
    info = game()
    info['gameDuration'] = 220
    for p in info['participants']:
        p['gameEndedInEarlySurrender'] = False
        p['gameEndedInSurrender'] = True
    data = {'matches': [{'id': 'short', 'score': 25, 'championId': 1, 'duration': 220}], 'champions': []}
    details = {'short': {'raw': {'info': info}, 'puuid': 'p0'}}
    result = calibration_report(data, details=details)
    assert result['shortGames'][0]['earlySurrender'] == 'No'
    assert result['shortGames'][0]['surrender'] == 'Yes'
    assert result['shortGames'][0]['scoreReason'] is None
    info['participants'][0]['gameEndedInEarlySurrender'] = True
    result = calibration_report(data, details=details)
    assert result['shortGames'][0]['earlySurrender'] == 'Yes'
    assert result['shortGames'][0]['scoreReason']
    assert result['componentGames'] == 0
    assert result['investigation']['comparisons'][0]['current'] is None
    del info['participants'][0]['gameEndedInEarlySurrender']
    result = calibration_report(data, details=details)
    assert result['shortGames'][0]['earlySurrender'] == 'Unknown'
