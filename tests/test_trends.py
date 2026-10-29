from app.trends import performance_trends, period_stats, DAY


def test_period_boundaries_filters_and_empty_weeks():
    now=2_000_000_000
    def match(age,score,role='TOP',champion=1):
        return {'playedAt':(now-age*DAY)*1000,'championId':champion,'role':role,'score':score,'win':True,'duration':1200,'deaths':4,'damage':12000,'vision':10}
    data={'matches':[match(0,80),match(30,60),match(30.001,40),match(60,20),match(61,100),match(1,0,'UTILITY',2)],'champions':[{'championId':1,'name':'Annie'}]}
    result=performance_trends(data,now,'TOP',1)
    assert result['current']['score']['value']==70
    assert result['previous']['score']['value']==30
    assert result['deltas']['score']==40
    assert result['current']['total']==2
    assert result['forms'][0]['form']=='insufficient'
    assert len(result['weeks'])==12
    assert any(w['score']['value'] is None for w in result['weeks'])


def test_rates_use_only_covered_minutes_and_zero_is_valid():
    stats=period_stats([{'score':0,'win':False,'duration':600,'damage':10000,'deaths':2},
                        {'score':100,'win':True,'duration':1200,'damage':10000,'vision':0,'deaths':0},
                        {'score':None,'win':True,'duration':600}])
    assert stats['score']=={'value':50,'count':2}
    assert stats['damage']=={'value':666.67,'count':2}
    assert stats['vision']=={'value':0,'count':1}
    assert stats['deaths']=={'value':1,'count':2}
    assert period_stats([])['score']['value'] is None


def test_champion_form_needs_three_samples_in_both_periods():
    now=2_000_000_000
    matches=[{'championId':1,'playedAt':(now-age*DAY)*1000,'score':score} for age,score in [(1,80)]*3+[(31,60)]*3]
    result=performance_trends({'matches':matches,'champions':[{'championId':1,'name':'Annie'}]},now)
    assert result['forms'][0]['form']=='improving'
    assert result['forms'][0]['delta']==20


def test_game_windows_apply_filters_before_slicing_and_include_unscored_slots():
    now = 2_000_000_000
    matches = [{'id': str(i), 'playedAt': (now - (i + 1) * DAY) * 1000, 'championId': 1,
                'role': 'TOP', 'score': None if i == 0 else (80 if i < 30 else 40),
                'win': i < 30, 'duration': 1200} for i in range(70)]
    matches += [{'id': 'excluded-role', 'playedAt': now * 1000, 'championId': 1, 'role': 'UTILITY', 'score': 0},
                {'id': 'excluded-champion', 'playedAt': now * 1000, 'championId': 2, 'role': 'TOP', 'score': 0},
                {'id': 'future', 'playedAt': (now + DAY) * 1000, 'championId': 1, 'role': 'TOP', 'score': 0}]
    data = {'matches': list(reversed(matches)), 'champions': [{'championId': 1, 'name': 'Annie'}]}
    result = performance_trends(data, now, 'TOP', 1, 'games')
    assert result['comparison'] == 'games'
    assert result['current']['total'] == result['previous']['total'] == 30
    assert result['current']['score'] == {'value': 80, 'count': 29}
    assert result['previous']['score'] == {'value': 40, 'count': 30}
    assert result['forms'][0]['delta'] == 40
    assert result['current']['winRate']['value'] == 100
    assert result['previous']['winRate']['value'] == 0
    assert result['weeks'] == performance_trends(data, now, 'TOP', 1, 'days')['weeks']


def test_game_windows_show_partial_and_empty_samples_without_inventing_values():
    now = 2_000_000_000
    matches = [{'id': str(i), 'playedAt': (now - i - 1) * 1000, 'championId': 1, 'score': 0} for i in range(35)]
    data = {'matches': matches}
    result = performance_trends(data, now, comparison='games')
    assert result['current']['total'] == 30 and result['previous']['total'] == 5
    assert result['current']['score']['value'] == 0
    short = performance_trends({'matches': matches[:4]}, now, comparison='games')
    assert short['current']['total'] == 4 and short['previous']['total'] == 0
    assert short['deltas']['score'] is None
    assert performance_trends({'matches': []}, now, comparison='games')['current']['total'] == 0


def test_game_timestamp_ties_use_match_id_for_stable_windows():
    now = 2_000_000_000
    matches = [{'id': f'{i:02}', 'playedAt': (now-1)*1000, 'championId': 1, 'score': i} for i in range(60)]
    a = performance_trends({'matches': matches}, now, comparison='games')
    b = performance_trends({'matches': list(reversed(matches))}, now, comparison='games')
    assert a == b
    assert a['current']['score']['value'] == 14.5
    assert a['previous']['score']['value'] == 44.5


def test_trends_endpoint_forwards_comparison(monkeypatch):
    import app.main as main
    async def dashboard(queue):
        return {'matches': [], 'queue': queue}
    monkeypatch.setattr(main, 'get_dashboard', dashboard)
    request = main.get_trends(queue='solo', role='TOP', champion=0, comparison='games', size=50)
    try:
        request.send(None)
    except StopIteration as finished:
        result = finished.value
    else:
        raise AssertionError('Mock endpoint unexpectedly suspended')
    assert result['comparison'] == 'games' and result['queue'] == 'solo' and result['size'] == 50



def test_selectable_game_window_sizes_and_partial_history():
    now = 2_000_000_000
    matches = [{'id': str(i), 'playedAt': (now-i-1)*1000, 'championId': 1,
                'score': 80 if i < 100 else 20} for i in range(220)]
    for size in (30, 50, 100):
        result = performance_trends({'matches': matches}, now, comparison='games', size=size)
        assert result['size'] == size
        assert result['current']['total'] == result['previous']['total'] == size
    result = performance_trends({'matches': matches}, now, comparison='games', size=100)
    assert result['current']['score']['value'] == 80
    assert result['previous']['score']['value'] == 20
    partial = performance_trends({'matches': matches[:120]}, now, comparison='games', size=100)
    assert partial['current']['total'] == 100 and partial['previous']['total'] == 20


def test_selectable_day_windows_include_exact_boundaries_and_leave_weeks_unchanged():
    now = 2_000_000_000
    for size in (50, 100):
        matches = [{'id': str(i), 'playedAt': (now-age*DAY)*1000, 'championId': 1, 'score': score}
                   for i, (age, score) in enumerate([(0, 80), (size, 60), (size+.1, 40), (2*size, 20), (2*size+1, 0)])]
        data = {'matches': matches}
        result = performance_trends(data, now, size=size)
        assert result['current']['score']['value'] == 70
        assert result['previous']['score']['value'] == 30
        assert result['current']['total'] == result['previous']['total'] == 2
        assert result['weeks'] == performance_trends(data, now)['weeks']


def test_invalid_comparison_sizes_are_rejected():
    import pytest
    for size in (0, -1, 31, 1000, True, '50'):
        with pytest.raises(ValueError):
            performance_trends({'matches': []}, 2_000_000_000, size=size)
