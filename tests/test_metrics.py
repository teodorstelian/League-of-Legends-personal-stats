from app.metrics import render_metrics


def test_metrics_empty_and_escaped_labels():
    empty = render_metrics('Name"\\\n#EU', [])
    assert 'lol_saved_games{player="Name\\"\\\\\\n#EU",queue="all"} 0.0' in empty
    assert 'lol_win_rate_percent{' not in empty


def test_metrics_averages_include_zero_and_skip_missing_scores():
    matches = [dict(champion='Ahri', queue=420, win=True, kills=4, deaths=0,
                    assists=6, score=0, playedAt=10000),
               dict(champion='Lux', queue=440, win=False, kills=2, deaths=2,
                    assists=4, score=None, playedAt=20000)]
    result = render_metrics('Main#EU', matches)
    assert 'lol_win_rate_percent{player="Main#EU",queue="all"} 50.0' in result
    assert 'lol_average_score{player="Main#EU",queue="all"} 0.0' in result
    assert 'lol_scored_games{player="Main#EU",queue="all"} 1.0' in result
    assert 'lol_latest_match_timestamp_seconds{player="Main#EU"} 20.0' in result
    assert 'lol_champion_score{player="Main#EU",champion="Lux"}' not in result


def test_mastery_snapshot_and_missing_data():
    missing = render_metrics('Main#EU', [])
    assert 'lol_mastery_available{player="Main#EU"} 0.0' in missing
    assert 'lol_mastery_combined_points{' not in missing
    result = render_metrics('Main#EU', [], {'mastery': [
        {'championId': 17, 'name': 'Teemo', 'points': 123456, 'level': 12},
        {'championId': 1, 'name': 'Annie', 'points': 0, 'level': 0},
    ]})
    assert 'lol_mastery_points{player="Main#EU",champion="Teemo",champion_id="17"} 123456.0' in result
    assert 'lol_mastery_level{player="Main#EU",champion="Teemo",champion_id="17"} 12.0' in result
    assert 'lol_mastery_combined_points{player="Main#EU"} 123456.0' in result
    assert 'lol_mastery_champions{player="Main#EU"} 1.0' in result
    empty = render_metrics('Main#EU', [], {'mastery': []})
    assert 'lol_mastery_available{player="Main#EU"} 1.0' in empty
    assert 'lol_mastery_combined_points{player="Main#EU"} 0.0' in empty


def test_champion_details_use_ids_queues_and_covered_samples():
    matches = [dict(champion='Chogath', championId=31, queue=420, win=True,
                    kills=4, deaths=0, assists=6, score=0, playedAt=10000),
               dict(champion='Chogath', championId=31, queue=440, win=False,
                    kills=2, deaths=2, assists=4, score=None, playedAt=20000)]
    result = render_metrics('Main#EU', matches, {'mastery': [
        {'championId': 31, 'name': "Cho'Gath", 'points': 100, 'level': 2}]})
    labels = 'player="Main#EU",champion="Cho\'Gath",champion_id="31",queue="all"'
    assert f'lol_champion_detail_games{{{labels}}} 2.0' in result
    assert f'lol_champion_detail_wins{{{labels}}} 1.0' in result
    assert f'lol_champion_detail_losses{{{labels}}} 1.0' in result
    assert f'lol_champion_detail_kills{{{labels}}} 3.0' in result
    assert f'lol_champion_detail_deaths{{{labels}}} 1.0' in result
    assert f'lol_champion_detail_score{{{labels}}} 0.0' in result
    assert f'lol_champion_detail_scored_games{{{labels}}} 1.0' in result
    assert 'lol_champion_detail_games{'+labels.replace('queue="all"','queue="solo"')+'} 1.0' in result
    assert 'lol_champion_detail_score{'+labels.replace('queue="all"','queue="flex"')+'}' not in result


def test_role_metrics_keep_unknown_and_weight_samples_correctly():
    matches = [dict(champion='Ahri', championId=103, queue=420, role='MIDDLE', win=True,
                    kills=4, deaths=0, assists=6, score=0, playedAt=10000),
               dict(champion='Ahri', championId=103, queue=420, role='MIDDLE', win=False,
                    kills=2, deaths=2, assists=4, score=None, playedAt=20000),
               dict(champion='Ahri', championId=103, queue=440, role='', win=True,
                    kills=9, deaths=3, assists=5, score=90, playedAt=30000),
               dict(champion='Lux', championId=99, queue=420, role='UTILITY', win=False,
                    kills=1, deaths=4, assists=10, score=60, playedAt=40000)]
    result = render_metrics('Main#EU', matches)
    labels = 'player="Main#EU",queue="all",role="all"'
    assert f'lol_role_games{{{labels}}} 4.0' in result
    assert f'lol_role_score{{{labels}}} 50.0' in result
    assert f'lol_role_scored_games{{{labels}}} 3.0' in result
    assert 'lol_role_games{player="Main#EU",queue="all",role="UNKNOWN"} 1.0' in result
    assert 'lol_role_games{player="Main#EU",queue="solo",role="UNKNOWN"} 0.0' in result
    cl = 'player="Main#EU",champion="Ahri",champion_id="103",queue="solo",role="MIDDLE"'
    assert f'lol_champion_role_games{{{cl}}} 2.0' in result
    assert f'lol_champion_role_kills{{{cl}}} 3.0' in result
    assert f'lol_champion_role_score{{{cl}}} 0.0' in result
    assert f'lol_champion_role_scored_games{{{cl}}} 1.0' in result
    assert 'lol_champion_role_games{player="Main#EU",champion="Ahri",champion_id="103",queue="solo",role="TOP"}' not in result
