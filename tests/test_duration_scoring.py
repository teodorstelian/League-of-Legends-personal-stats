import pytest
from app.duration import SLOPES, reference_multiplier
from app.scoring import VERSION, score_player, curve_score, CURVES, exceptional_score
from test_scoring import game


def test_frozen_references_are_bounded_and_have_30_minute_anchor():
    assert len(SLOPES) == 63
    for key in SLOPES:
        assert reference_multiplier(*key, 30) == 1
        for minutes in (0, 5, 10, 20, 40, 50, 1000):
            assert .7 <= reference_multiplier(*key, minutes) <= 1.3
        assert reference_multiplier(*key, 5) == reference_multiplier(*key, 10)
        assert reference_multiplier(*key, 100) == reference_multiplier(*key, 50)
    assert reference_multiplier('UNKNOWN', 'unknown', 'Champion damage', 15) == 1
    assert all(key[2] not in ('Survival', 'Kill participation') for key in SLOPES)


def test_active_candidate_matches_frozen_component_formula_and_has_rollback():
    info = game()
    info['gameDuration'] = 1200
    p = info['participants'][2]
    active = score_player(info, p, ['Mage'])
    previous = score_player(info, p, ['Mage'], duration_adjustment=False)
    assert active['version'] == VERSION
    assert previous['version'] == '4'
    assert active['baselineValue'] == previous['value']
    old_components = {c['name']: c for c in previous['components']}
    adjusted = []
    for c in active['components']:
        old = old_components[c['name']]
        multiplier = reference_multiplier('MIDDLE', active['archetype'], c['name'], 20)
        assert c['target'] == pytest.approx(old['target'] * multiplier, abs=.0001)
        assert c['weight'] == old['weight']
        assert c['own'] == old['own']
        expected = (curve_score if c['name'] == 'Survival' else exceptional_score)(c['own'] / (old['target'] * multiplier), CURVES[c['name']])
        if c['name'] != 'Survival':
            normal = curve_score(c['own'] / (old['target'] * multiplier), CURVES[c['name']])
            expected = normal + (expected - normal) * (c['maximum'] - 100) / 20
        assert c['value'] == pytest.approx(expected, abs=.1)
        if multiplier != 1:
            adjusted.append(c)
    assert adjusted
    assert 0 <= active['value'] <= 100


def test_thirty_minute_and_unmodeled_scores_preserve_v4():
    info = game()
    for tags in (None, ['Mage'], ['Tank']):
        active = score_player(info, info['participants'][2], tags)
        baseline = score_player(info, info['participants'][2], tags, duration_adjustment=False)
        assert active['withoutExceptional'] == baseline['value']
    info['gameDuration'] = 1200
    assert score_player(info, info['participants'][0])['withoutExceptional'] == score_player(info, info['participants'][0], duration_adjustment=False)['value']
