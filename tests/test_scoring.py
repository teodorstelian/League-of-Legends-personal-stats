from app.scoring import score_player


def game():
    return {'gameMode': 'CLASSIC', 'gameDuration': 1800, 'gameVersion': '16.20.1',
            'gameStartTimestamp': 100, 'participants': [
        {'puuid': f'p{i}', 'championName': 'Annie', 'championId': 1,
         'teamId': 100 if i < 5 else 200, 'teamPosition': ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'][i % 5],
         'kills': 5, 'deaths': 5, 'assists': 5, 'win': i < 5,
         'totalDamageDealtToChampions': 20000, 'goldEarned': 10000, 'visionScore': 20,
         'damageDealtToObjectives': 5000, 'totalHealsOnTeammates': 1000,
         'totalDamageShieldedOnTeammates': 1000, 'item0': 1001, 'summoner1Id': 4,
         'perks': {'styles': [{'selections': [{'perk': 8005}]}]}}
        for i in range(10)]}


def test_equal_performance_is_50_and_win_does_not_change_score():
    info = game()
    assert score_player(info, info['participants'][0])['value'] == 50
    assert score_player(info, info['participants'][5])['value'] == 50


def test_improving_damage_or_survival_increases_score():
    info = game()
    p = info['participants'][0]
    p['totalDamageDealtToChampions'] *= 4
    assert score_player(info, p)['value'] > 50
    p['deaths'] = 0
    score = score_player(info, p)
    assert 50 < score['value'] <= 100
    assert sum(c['weight'] for c in score['components']) == 100


def test_support_impact_and_aram_rules():
    info = game()
    p = info['participants'][4]
    score = score_player(info, p)
    assert score['components'][0]['name'] == 'Teamfight impact'
    p['totalHealsOnTeammates'] = 50000
    assert score_player(info, p)['value'] > 50
    info['gameMode'] = 'ARAM'
    score = score_player(info, p)
    assert score['comparison'] == 'Average of the opposing team'
    assert len(score['components']) == 4
    assert not any(c['name'] in ('Vision', 'Objective pressure') for c in score['components'])


def test_missing_metrics_zeroes_and_remakes():
    info = game()
    for p in info['participants']:
        p['deaths'] = 0
        p['damageDealtToObjectives'] = 0
    assert score_player(info, info['participants'][0])['value'] == 50
    del info['participants'][0]['visionScore']
    score = score_player(info, info['participants'][0])
    assert len(score['components']) == 5
    assert score['value'] == 50
    info['gameDuration'] = 90
    assert score_player(info, info['participants'][0])['value'] is None


def test_unsupported_modes_are_not_scored():
    info = game()
    info['gameMode'] = 'CHERRY'
    assert score_player(info, info['participants'][0])['value'] is None
