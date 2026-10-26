from app.references import resolve_reference
from app.scoring import VERSION, score_player
from app.timeline import economy_checkpoints
from test_scoring import game


def catalog(samples=100, **extra):
    return {'enabled': True, 'records': [{'champion': 'Annie', 'role': 'TOP', 'metric': 'Champion damage',
        'rate': 1200, 'samples': samples, 'source': 'Independent test reference', 'independentOfRatedPlayers': True, **extra}]}


def test_reference_shrinkage_and_safe_fallbacks():
    args = ('Annie', 'TOP', 'Champion damage', 1000)
    result = resolve_reference(*args, catalog=catalog())
    assert result['rate'] == 1100 and result['blend'] == .5
    assert resolve_reference(*args, catalog=catalog(29))['rate'] == 1000
    assert resolve_reference(*args, catalog=catalog(independentOfRatedPlayers=False))['rate'] == 1000
    assert resolve_reference(*args, catalog=catalog(rate=float('nan')))['rate'] == 1000
    assert resolve_reference(*args, catalog=catalog(rate=-1))['rate'] == 1000
    duplicate = catalog(); duplicate['records'] *= 2
    assert resolve_reference(*args, catalog=duplicate)['rate'] == 1000
    assert resolve_reference('Unknown', *args[1:], catalog=catalog())['rate'] == 1000
    assert resolve_reference('Annie', 'TOP', 'Economy', 500, catalog=catalog())['rate'] == 500


def test_reviewed_caps_and_context_do_not_change_survival_or_weights():
    info = game(); p = info['participants'][0]
    p.update(totalDamageDealtToChampions=1000000, goldEarned=1000000, visionScore=10000, assists=100, damageDealtToObjectives=1000000, timeCCingOthers=1000000)
    active = score_player(info, p, ['Tank'])
    legacy = score_player(info, p, ['Tank'], reviewed_policy=False)
    assert active['version'] == VERSION and legacy['version'] != VERSION
    a = {c['name']: c for c in active['components']}
    b = {c['name']: c for c in legacy['components']}
    assert a['Champion damage']['maximum'] == 125
    assert a['Crowd control']['maximum'] == 125
    assert a['Crowd control']['value'] == 125
    assert a['Economy']['value'] == 125
    assert a['Vision']['value'] == 125
    for metric in ('Economy', 'Vision', 'Kill participation', 'Objective pressure', 'Survival'):
        assert a[metric]['maximum'] == (100 if metric == 'Survival' else 125)
    for name in a:
        assert a[name]['weight'] == b[name]['weight']
    assert a['Survival']['value'] == b['Survival']['value']
    assert active['economyContext']['affectsScore'] is False
    assert economy_checkpoints(None, {}) == []
    assert economy_checkpoints({'unavailable': True}, {}) == []
