import pytest
from app.scoring import CURVES, exceptional_score, score_player
from test_scoring import game


def test_exceptional_tail_is_continuous_diminishing_and_capped():
    anchors = CURVES['Champion damage']
    full = anchors[-1][0]
    assert exceptional_score(full, anchors) == 100
    assert exceptional_score(full + 1e-9, anchors) == pytest.approx(100)
    assert exceptional_score(full * 1.25, anchors) == 110
    assert exceptional_score(full * 1.5, anchors) == 116
    assert exceptional_score(full * 2, anchors) == 120
    assert exceptional_score(full * 100, anchors) == 120
    values = [exceptional_score(i / 100, anchors) for i in range(501)]
    assert values == sorted(values)
    assert all(0 <= v <= 120 for v in values)


def test_damage_bonus_retains_weight_and_final_cap_and_survival_has_no_bonus():
    info = game()
    p = info['participants'][0]
    p['totalDamageDealtToChampions'] = 1000000
    ordinary = score_player(info, p, ['Marksman'], exceptional_output=False)
    extra = score_player(info, p, ['Marksman'])
    damage = next(c for c in extra['components'] if c['name'] == 'Champion damage')
    survival = next(c for c in extra['components'] if c['name'] == 'Survival')
    assert damage['value'] == 120 and damage['weight'] == 30
    assert damage['bonusContribution'] == 6
    assert extra['value'] - ordinary['value'] == pytest.approx(6, abs=.1)
    assert survival['bonus'] == 0 and survival['maximum'] == 100
    for q in info['participants']:
        q.update(assists=100, deaths=0, visionScore=10000, goldEarned=1000000, damageDealtToObjectives=1000000)
    capped = score_player(info, p, ['Marksman'])
    assert capped['value'] == 100
    assert all(c['missedPoints'] >= 0 for c in capped['components'])
    assert all(0 <= c['value'] <= c['maximum'] for c in capped['components'])
