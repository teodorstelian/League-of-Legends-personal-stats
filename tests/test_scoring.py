from app.scoring import score_player


def game():
    return {'gameMode': 'CLASSIC', 'queueId': 420, 'gameDuration': 1800, 'gameVersion': '16.20.1',
            'gameStartTimestamp': 100, 'participants': [
        {'puuid': f'p{i}', 'championName': 'Annie', 'championId': 1,
         'teamId': 100 if i < 5 else 200, 'teamPosition': ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'][i % 5],
         'kills': 5, 'deaths': 5, 'assists': 5, 'win': i < 5,
         'totalDamageDealtToChampions': 20000, 'goldEarned': 10000, 'visionScore': 20,
         'damageDealtToObjectives': 5000, 'totalHealsOnTeammates': 1000,
         'totalDamageShieldedOnTeammates': 1000, 'item0': 1001, 'summoner1Id': 4,
         'perks': {'styles': [{'selections': [{'perk': 8005}]}]}}
        for i in range(10)]}


def test_opponent_and_win_do_not_change_score():
    info = game()
    p = info['participants'][0]
    baseline = score_player(info, p)['value']
    info['participants'][5].update(totalDamageDealtToChampions=999999, kills=100, deaths=0, visionScore=200)
    p['win'] = False
    assert score_player(info, p)['value'] == baseline


def test_improving_damage_or_survival_increases_score():
    info = game()
    p = info['participants'][0]
    baseline = score_player(info, p)['value']
    p['totalDamageDealtToChampions'] *= 4
    assert score_player(info, p)['value'] > baseline
    p['deaths'] = 0
    score = score_player(info, p)
    assert 50 < score['value'] <= 100
    assert sum(c['weight'] for c in score['components']) == 100


def test_support_impact_and_aram_rules():
    info = game()
    p = info['participants'][4]
    score = score_player(info, p)
    assert score['components'][0]['name'] == 'Support impact'
    p['totalHealsOnTeammates'] = 50000
    assert score_player(info, p)['value'] > 50
    info['gameMode'] = 'ARAM'
    score = score_player(info, p)
    assert score['opponentContext'] == 'Opposing team average'
    assert len(score['components']) == 4
    assert not any(c['name'] in ('Vision', 'Objective pressure') for c in score['components'])


def test_missing_metrics_zeroes_and_remakes():
    info = game()
    for p in info['participants']:
        p['deaths'] = 0
        p['damageDealtToObjectives'] = 0
    assert 0 <= score_player(info, info['participants'][0])['value'] <= 100
    del info['participants'][0]['visionScore']
    score = score_player(info, info['participants'][0])
    assert len(score['components']) == 5
    assert score['value'] is not None
    info['gameDuration'] = 90
    assert score_player(info, info['participants'][0])['value'] is None


def test_unsupported_modes_are_not_scored():
    info = game()
    info['gameMode'] = 'CHERRY'
    assert score_player(info, info['participants'][0])['value'] is None


def test_both_opponents_can_independently_earn_100():
    info = game()
    for index in (0, 5):
        info['participants'][index].update(totalDamageDealtToChampions=30000, goldEarned=15000,
            assists=20, deaths=0, visionScore=36, damageDealtToObjectives=30000)
    assert score_player(info, info['participants'][0])['value'] == 100
    assert score_player(info, info['participants'][5])['value'] == 100


def test_equal_rates_score_equally_across_duration():
    info = game()
    before = score_player(info, info['participants'][0])['value']
    info['gameDuration'] *= 2
    for p in info['participants']:
        for field in ['kills','deaths','assists','goldEarned','totalDamageDealtToChampions','visionScore','damageDealtToObjectives']:
            p[field] *= 2
    assert score_player(info, info['participants'][0])['value'] == before


def test_too_many_missing_metrics_do_not_produce_a_perfect_score():
    info = game()
    p = info['participants'][0]
    for field in ['goldEarned','visionScore','damageDealtToObjectives','totalDamageDealtToChampions']:
        del p[field]
    assert score_player(info, p)['value'] is None


def test_damage_support_does_not_need_healing_and_gets_damage_weights():
    info = game()
    p = info['participants'][4]
    p['championName'] = 'Zyra'
    del p['totalHealsOnTeammates']
    del p['totalDamageShieldedOnTeammates']
    score = score_player(info,p,['Mage','Support'])
    assert score['archetype'] == 'Damage support'
    assert score['components'][0]['name'] == 'Champion damage'
    assert score['components'][0]['weight'] == 30
    assert score['value'] is not None


def test_tank_emphasizes_cc_without_rewarding_damage_taken():
    info = game()
    p = info['participants'][1]
    p['timeCCingOthers'] = 45
    score = score_player(info,p,['Tank','Mage'])
    assert score['archetype'] == 'Tank'
    cc=next(c for c in score['components'] if c['name']=='Crowd control')
    assert cc['weight']==15 and cc['value']==100
    p['totalDamageTaken']=999999
    assert score_player(info,p,['Tank','Mage'])['value']==score['value']
    assert len(score['explanations']['strengths'])==2


def test_split_profile_only_applies_in_solo_lanes():
    info=game()
    p=info['participants'][0]
    p.update(championName='Yorick',damageDealtToTurrets=18000)
    score=score_player(info,p,['Fighter','Tank'])
    assert score['archetype']=='Split-pusher'
    tower=next(c for c in score['components'] if c['name']=='Tower pressure')
    assert tower['weight']==30 and tower['value']==100
    p['teamPosition']='JUNGLE'
    assert score_player(info,p,['Fighter','Tank'])['archetype']=='Fighter'


def test_carry_and_fallback_profiles_are_explicit():
    info=game();p=info['participants'][0]
    assert score_player(info,p,['Marksman'])['components'][0]['weight']==30
    assert 'unavailable' in score_player(info,p)['archetype']
    assert score_player(info,p,['Support','Marksman'])['archetype']=='Marksman carry'
    assert score_player(info,p,['Support'])['archetype']=='Role baseline (unmapped tags)'
