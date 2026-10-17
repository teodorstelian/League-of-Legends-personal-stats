from app.statistics import enrich_dashboard, lane_averages, score_average, champion_tiers


def test_averages_include_zero_and_exclude_unscored_invalid_values():
    matches = [{'score': s} for s in [0, 100, None, float('nan'), True, -1, 101]]
    assert score_average(matches) == {'average': 50.0, 'scored': 2, 'total': 7}
    assert score_average([]) == {'average': None, 'scored': 0, 'total': 0}


def test_champion_and_lane_averages_are_weighted_by_games():
    matches = [{'championId': 1, 'score': 30, 'role': 'TOP'},
               {'championId': 1, 'score': 60, 'role': 'UTILITY'},
               {'championId': 2, 'score': 90, 'role': 'TOP'},
               {'championId': 1, 'score': None, 'role': 'TOP'}]
    source = {'matches': matches, 'champions': [{'championId': 1}, {'championId': 2}, {'championId': 3}], 'mastery': [{'championId': 1}]}
    result = enrich_dashboard(source)
    assert result['scoreStats'] == {'average': 60, 'scored': 3, 'total': 4}
    assert result['champions'][0]['scoreStats'] == {'average': 45, 'scored': 2, 'total': 3}
    assert result['champions'][2]['scoreStats']['average'] is None
    assert result['mastery'][0]['scoreStats']['average'] == 45
    assert 'scoreStats' not in source['champions'][0]
    lanes = {lane['lane']: lane for lane in result['lanes']}
    assert lanes['TOP']['average'] == 60
    assert lanes['TOP']['scored'] == 2
    assert lanes['UTILITY']['average'] == 60
    assert lanes['JUNGLE']['average'] is None


def test_aram_never_counts_as_a_lane_and_missing_roles_are_visible():
    lanes = {lane['lane']: lane for lane in lane_averages([
        {'score': 80, 'mode': 'ARAM', 'role': 'TOP'}, {'score': 40}])}
    assert lanes['TOP']['total'] == 0
    assert lanes['ARAM']['average'] == 80
    assert lanes['UNKNOWN']['average'] == 40


def test_tier_boundaries_role_isolation_and_minimum_samples():
    matches = [{'championId': i, 'score': score, 'role': 'TOP', 'win': True}
               for i, score in enumerate([75, 60, 50, 40, 39.9], 1)]
    matches += [{'championId': 1, 'score': 20, 'role': 'BOTTOM'},
                {'championId': 6, 'score': None, 'role': 'TOP'},
                {'championId': 7, 'score': 100, 'role': 'UNKNOWN'}]
    data = {'matches': matches, 'champions': [{'championId': i, 'name': str(i)} for i in range(1,8)], 'queue':'solo'}
    result = champion_tiers(data, 1)
    assert len(result['roles']) == 5
    assert result['queue'] == 'solo'
    assert result['unknownRoleGames'] == 1
    top = result['roles'][0]
    assert [t['champions'][0]['championId'] for t in top['tiers']] == [1,2,3,4,5]
    assert top['provisional'][0]['championId'] == 6
    bot = result['roles'][3]
    assert bot['tiers'][-1]['champions'][0]['scoreStats']['average'] == 20
    assert all(not t['champions'] for t in champion_tiers(data, 3)['roles'][0]['tiers'])
