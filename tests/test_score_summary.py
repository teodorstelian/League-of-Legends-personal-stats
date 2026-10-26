import pytest
from app.scoring import score_player
from test_scoring import game


def test_summary_equation_and_selected_components_are_consistent():
    info = game()
    p = info['participants'][0]
    p['totalDamageDealtToChampions'] = 1000000
    result = score_player(info, p, ['Marksman'])
    assert result['withoutExceptional'] + result['exceptionalBonus'] == pytest.approx(result['value'], abs=.001)
    assert result['summary']['strength']['contribution'] == max(c['contribution'] for c in result['components'])
    assert result['summary']['improvement']['missedPoints'] == max(c['missedPoints'] for c in result['components'])
    assert 'experimental' not in result['method'].lower()
    assert 'provisional' not in result['comparison'].lower()


def test_effective_bonus_respects_final_cap_and_full_scores_have_no_gap():
    info = game()
    for p in info['participants']:
        p.update(totalDamageDealtToChampions=1000000, goldEarned=1000000, deaths=0,
                 assists=100, visionScore=10000, damageDealtToObjectives=1000000)
    result = score_player(info, info['participants'][0], ['Marksman'])
    assert result['value'] == 100
    assert result['withoutExceptional'] + result['exceptionalBonus'] == pytest.approx(100)
    assert result['summary']['improvement'] is None
    info['gameDuration'] = 90
    assert score_player(info, info['participants'][0])['value'] is None
